import cv2
# from scipy import ndimage
# from skimage.feature import peak_local_max
# from skimage.morphology import watershed
# from numpy import linalg
import numpy as np
from scipy.optimize import minimize

from atlasbuggy.camera.pipeline import Pipeline


class CalibrationPipeline(Pipeline):
    def __init__(self, enabled=True, log_level=None):
        super(CalibrationPipeline, self).__init__(enabled, log_level)

        self.square_size = 26.715  # mm squares
        self.pattern_size = (7, 7)  # number of corners

        self.pattern_points = np.zeros((np.prod(self.pattern_size), 3), np.float32)
        self.pattern_points[:, :2] = np.indices(self.pattern_size).T.reshape(-1, 2)
        self.pattern_points *= self.square_size

        self.obj_points = []
        self.img_points = []

        self.results_service_tag = "results"
        self.add_service(self.results_service_tag, self.results_post_service)

    def results_post_service(self, data):
        return data

    def pipeline(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        found, corners = cv2.findChessboardCorners(gray, self.pattern_size)
        if found:
            term = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_COUNT, 30, 0.1)
            cv2.cornerSubPix(gray, corners, (5, 5), (-1, -1), term)

            if self.current_frame_num % 10 == 0:
                self.img_points.append(corners.reshape(-1, 2))
                self.obj_points.append(self.pattern_points)
                print("Chessboard found! length: %s" % len(self.img_points))

                if len(self.img_points) >= 25:
                    self.exit()
        else:
            print("Chessboard not found")

        cv2.drawChessboardCorners(frame, self.pattern_size, corners, found)
        return frame

    def stopped(self):
        rms, camera_matrix, dist_coefs, rvecs, tvecs = cv2.calibrateCamera(self.obj_points, self.img_points,
                                                                           (self.width, self.height), None, None)
        print("\nRMS:", rms)
        print("camera matrix:\n", camera_matrix)
        print("distortion coefficients: ", dist_coefs.ravel())


class NaborisPipeline(Pipeline):
    def __init__(self, enabled=True, log_level=None):
        super(NaborisPipeline, self).__init__(enabled, log_level)

        self.left_distance = 0
        self.right_distance = 0
        self.forward_distance = 0

        self.wall_detector = WallDetector()
        self.odometer = VisualOdometer()

        self.results_service_tag = "results"
        self.add_service(self.results_service_tag, self.results_post_service)

    def results_post_service(self, data):
        return data

    def pipeline(self, frame):
        original_frame = frame.copy()
        # frame = self.wall_detector.detect_walls(original_frame, frame)
        frame = self.odometer.update(original_frame, frame)
        return frame


class WallDetector:
    def __init__(self):
        self.morph_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))

        self.k_means_criteria = (cv2.TERM_CRITERIA_MAX_ITER + cv2.TERM_CRITERIA_EPS, 10, 1.0)
        self.num_clusters_k = 6

        # don't optimize for integer values. This is considered np-hard
        self.blur_value = 7
        self.laplacian_ksize = 3
        laplacian_scale = 1.0
        self.threshold_value = 10
        self.hough_line_threshold = 100
        hough_line_rho = 1.5
        hough_line_theta = np.pi / 180
        self.canny_low = 1
        self.canny_high = 100

        self.initial_guess = np.array(
            [laplacian_scale, hough_line_rho, hough_line_theta]
        )

        self.desired_line_num = 50
        self.max_line_num = 100

        self.current_frame = None
        self.draw_frame = None
        self.pipeline_frame = None
        self.hough_result = None
        self.has_guessed = False

    def detect_walls(self, frame, draw_frame):
        self.current_frame = frame
        self.draw_frame = draw_frame
        if not self.has_guessed:  # self.hough_result is None or len(self.hough_result) > self.max_line_num:
            print("before:", self.initial_guess)
            result = minimize(self.hough_pipeline, self.initial_guess, method='nelder-mead',
                              # tol=1E-9,
                              # options={'disp': True}
                              )
            # print(self.initial_guess == result.x)
            self.initial_guess = result.x
            print("after:", self.initial_guess)

            self.has_guessed = True
        else:
            self.hough_pipeline(self.initial_guess)

        if self.hough_result is not None:
            # print("result length:", len(self.hough_result))
            # for rho, theta in self.hough_result[:, 0]:
            #     self.draw_houghlines(frame, rho, theta, (0, 0, 255))

            if len(self.hough_result) < self.num_clusters_k:
                num_clusters_k = len(self.hough_result)
            else:
                num_clusters_k = self.num_clusters_k
            _, label, center = cv2.kmeans(self.hough_result, num_clusters_k, None, self.k_means_criteria, 10,
                                          cv2.KMEANS_RANDOM_CENTERS)
            for pt in center:
                # print(pt[1], end=", ")
                self.draw_houghlines(self.draw_frame, pt[0], pt[1], (0, 255, 255))

        # self.pipeline_frame = cv2.resize(self.pipeline_frame, (width, height))
        # self.pipeline_frame = cv2.cvtColor(self.pipeline_frame, cv2.COLOR_GRAY2BGR)
        self.pipeline_frame = cv2.bitwise_not(self.pipeline_frame)
        # return np.concatenate((frame, self.pipeline_frame), axis=1)
        return cv2.bitwise_and(self.draw_frame, self.draw_frame, mask=self.pipeline_frame)

    def hough_pipeline(self, x):
        laplacian_scale, hough_line_rho, hough_line_theta = x

        # blur_value = int(np.ceil(blur_value) // 2 * 2 + 1)
        # laplacian_ksize = int(np.ceil(laplacian_ksize) // 2 * 2 + 1)  # round to nearest odd number
        # threshold_value = np.clip(threshold_value, 0, 255)
        # hough_line_threshold = int(hough_line_threshold)

        gray = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2GRAY)
        # gray = cv2.GaussianBlur(gray, (self.blur_value, self.blur_value), 0)
        gray = cv2.medianBlur(gray, self.blur_value)

        laplacian_f = cv2.Laplacian(gray, cv2.CV_16S, ksize=self.laplacian_ksize, scale=laplacian_scale)
        abs_laplacian_f = np.absolute(laplacian_f)
        laplacian_8u = np.uint8(abs_laplacian_f)
        value, diff_frame = cv2.threshold(laplacian_8u, self.threshold_value, 255, cv2.THRESH_BINARY)

        opening = cv2.morphologyEx(diff_frame, cv2.MORPH_OPEN, self.morph_kernel, iterations=1)
        dilation = cv2.dilate(opening, self.morph_kernel, iterations=1)

        canny = cv2.Canny(dilation, self.canny_low, self.canny_high)

        self.hough_result = cv2.HoughLines(canny, rho=hough_line_rho, theta=hough_line_theta,
                                           threshold=self.hough_line_threshold)
        if self.hough_result is not None:
            function_result = (len(self.hough_result) - self.desired_line_num) ** 2
        else:
            function_result = self.desired_line_num ** 2

        self.pipeline_frame = dilation
        return function_result

    def draw_houghlines(self, frame, rho, theta, color):
        a = np.cos(theta)
        b = np.sin(theta)
        x0 = a * rho
        y0 = b * rho
        x1 = int(x0 + 1000 * -b)
        y1 = int(y0 + 1000 * a)
        x2 = int(x0 - 1000 * -b)
        y2 = int(y0 - 1000 * a)
        cv2.line(frame, (x1, y1), (x2, y2), color, 2)


class VisualOdometer:
    def __init__(self):
        self.focal_length = 700
        self.principle_point = 607.1928, 185.2157
        self.camera_matrix = np.array([[self.focal_length, 0, self.principle_point[0],
                                        0, self.focal_length, self.principle_point[1],
                                        0, 0, 1]])

        self.orb = cv2.ORB_create()
        self.current_points = None
        self.prev_points = None
        self.optical_flow_criteria = (cv2.TERM_CRITERIA_COUNT + cv2.TERM_CRITERIA_EPS, 30, 0.01)

        self.current_frame = None
        self.prev_frame = None

    def detect_features(self, frame):
        self.prev_points = self.current_points
        keypoints = self.orb.detect(frame, None)
        keypoints, descriptors = self.orb.compute(frame, keypoints)

        self.current_points = cv2.KeyPoint_convert(keypoints)
        return cv2.drawKeypoints(frame, keypoints, None, color=(0, 255, 0), flags=0)

    def track_features(self):
        self.current_points, status, error = \
            cv2.calcOpticalFlowPyrLK(self.prev_frame, self.current_frame, self.prev_points, self.current_points,
                                     None, None, (21, 21), 3, self.optical_flow_criteria, 0, 0.001)

        new_current_points = []
        new_prev_points = []
        for index in range(len(status)):
            point = self.current_points[index]
            if point.x < 0 or point.y < 0:
                status[0] = 0
            if status[0] != 0:
                new_current_points.append(point)
                new_prev_points.append(self.prev_points[index])

        self.current_points = new_current_points
        self.prev_points = new_prev_points

    def update(self, frame, draw_frame):
        frame = self.detect_features(frame)
        if self.prev_points is None:
            self.track_features()
        else:
            print(len(self.prev_points))
            E, mask = cv2.findEssentialMat(self.current_points, self.prev_points, focal=self.focal_length,
                                           pp=self.principle_point, method=cv2.RANSAC, prob=0.999, threshold=3.0)
            points, R, t, mask = cv2.recoverPose(E, self.current_points, self.prev_points)

            self.track_features()

        return frame

# self.skelton_kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
# @staticmethod
# def least_squares_intersection(a, n, transpose=True):
#     """
#     Return the point of intersection computed using the least-square method.
#     :param a: a list of point lying on the lines. Points are nx1 matrices
#     :param n: a list of line directions. Directions are nx1 matrices.
#     :param transpose: should transpose vectors? default true
#     :return: the point of intersection
#     """
#     assert (len(a) == len(n))  # same numbers of points as numbers of directions
#
#     if transpose:
#         n = map(lambda v: np.asmatrix(v / linalg.norm(v)).T, n)  # normalize directions and transpose
#         a = map(lambda v: np.asmatrix(v).T, a)  # transform into matrix and transpose
#     else:
#         n = map(lambda v: np.asmatrix(v / linalg.norm(v)).T, n)  # normalize directions
#         a = map(lambda v: np.asmatrix(v), a)  # transform into matrix
#
#     n_0 = next(n)
#     r = np.zeros((n_0.shape[0], n_0.shape[0]))
#     q = np.zeros((n_0.shape[0], 1))
#     for point, direction in zip(a, n):
#         ri = np.identity(direction.shape[0]) - direction.dot(direction.T)
#         qi = ri.dot(point)
#         r = r + ri
#         q = q + qi
#
#     return linalg.solve(r, q)

# unused:

# height, width = frame.shape[0:2]
# new_height = height // 3
# new_width = width // 6
# center_x = width // 2
# # center_y = height // 2
#
# frame = frame[height - new_height:  height, center_x - new_width: center_x + new_width]

# skeleton = np.zeros(dilation.shape, np.uint8)
# size = np.size(dilation)
# done = False
# while not done:
#     eroded = cv2.erode(dilation, self.skelton_kernel)
#     temp = cv2.dilate(eroded, self.skelton_kernel)
#     temp = cv2.subtract(dilation, temp)
#     skeleton = cv2.bitwise_or(dilation, temp)
#     dilation = eroded.copy()
#
#     zeros = size - cv2.countNonZero(dilation)
#     if zeros == size:
#         done = True

# mask = cv2.inRange(diff_frame, 240, 255)
# masked = cv2.bitwise_and(diff_frame, diff_frame, mask=mask)
#
# kernel = np.ones((5, 5), np.uint8)
# dilated = cv2.dilate(masked, kernel, iterations=1)

# erosion = cv2.erode(dilation, self.morph_kernel, iterations=1)

# intersection = self.least_squares_intersection(points, directions)
# intersection = tuple(np.int16(intersection.T).tolist()[0])
# print(intersection)
# cv2.circle(frame, intersection, 10, (255, 0, 0), 3)

# lines = cv2.HoughLinesP(canny, 1.2, np.pi / 180, 100, minLineLength=10, maxLineGap=25)
# if lines is not None:
#     for x1, y1, x2, y2 in lines[:, 0]:
#         cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

# self.post((self.left_distance, self.right_distance, self.forward_distance), self.results_service_tag)

# if cluster1 is not None or cluster2 is not None or center is not None:
