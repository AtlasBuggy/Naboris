import cv2
# from scipy import ndimage
# from skimage.feature import peak_local_max
# from skimage.morphology import watershed
# from numpy import linalg
import numpy as np
from scipy.optimize import minimize
from scipy.stats import norm

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
        print("distortion coefficients:\n", dist_coefs)
        print("rvecs:", rvecs)
        print("tvecs:", tvecs)


class NaborisPipeline(Pipeline):
    def __init__(self, enabled=True, log_level=None):
        super(NaborisPipeline, self).__init__(enabled, log_level)

        self.left_distance = 0
        self.right_distance = 0
        self.forward_distance = 0

        self.focal_length = 753.89072627, 746.98092088
        self.principle_point = 268.01003591, 131.86922614
        self.rms = 0.34601143374607224
        self.distortion_coefficients = np.array([[-0.20154387, 2.59173859, -0.03040153, -0.02874057, -6.8478438]])
        self.camera_matrix = np.array([[self.focal_length[0], 0, self.principle_point[0]],
                                       [0, self.focal_length[1], self.principle_point[1]],
                                       [0, 0, 1]])

        self.new_camera_matrix = None
        self.region_of_interest = None

        self.roi_frame = None

        self.wall_detector = None
        self.odometer = VisualOdometer(self.camera_matrix)

        self.results_service_tag = "results"
        self.add_service(self.results_service_tag, self.results_post_service)

    def start(self):
        self.new_camera_matrix, self.region_of_interest = cv2.getOptimalNewCameraMatrix(
            self.camera_matrix, self.distortion_coefficients, (self.width, self.height), 1, (self.width, self.height))
        self.roi_frame = np.zeros((self.height, self.width, 3))
        self.wall_detector = WallDetector(self.width, self.height, self.logger)

    def undistort(self, frame):
        return cv2.undistort(frame, self.camera_matrix, self.distortion_coefficients, None, self.new_camera_matrix)
        # x, y, w, h = self.region_of_interest
        # return frame[y: y + h, x: x + w]

    def results_post_service(self, data):
        return data

    def adjust_filter(self):
        self.wall_detector.adjust_filter()

    def pipeline(self, frame):
        original_frame = frame.copy()
        frame = self.wall_detector.detect_walls(original_frame, frame)
        # frame = self.odometer.update(original_frame, frame)

        self.post((self.odometer.position, self.odometer.rotation,
                   self.wall_detector.distances), service=self.results_service_tag)

        return frame

        # undistorted = self.undistort(frame)
        # height, width = undistorted.shape[0:2]
        # self.roi_frame[0:height, 0:width] = undistorted
        # return np.concatenate((self.roi_frame, frame), axis=1)


class WallDetector:
    def __init__(self, width, height, logger):
        self.logger = logger

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
        self.width = width
        self.height = height

        self.left_score = LineScore(self.height, self.height / 2)
        self.right_score = LineScore(self.height, self.height / 2)
        self.horz_score = LineScore(0.0, np.radians(10.0))
        self.scores = [self.left_score, self.right_score, self.horz_score]
        self.distances = [0.0, 0.0, 0.0]

        # self.vert_score_mean = np.pi / 2
        # self.vert_score_std = np.radians(10.0)
        # self.vert_normalized_value = norm.pdf(self.vert_score_mean, self.vert_score_mean, self.vert_score_std)

        self.min_score = 0.75

        self.current_frame = None
        self.draw_frame = None
        self.pipeline_frame = None
        self.hough_result = None
        self.has_guessed = False
        self.is_minimizing = False

    def adjust_filter(self):
        self.logger.info("before: %s" % self.initial_guess)
        self.is_minimizing = True
        result = minimize(self.hough_pipeline, self.initial_guess, method='nelder-mead',
                          tol=2,
                          options={'disp': True}
                          )
        self.is_minimizing = False
        # print(self.initial_guess == result.x)
        self.initial_guess = result.x
        self.logger.info("after: " % self.initial_guess)

    def detect_walls(self, frame, draw_frame):
        if not self.is_minimizing:
            self.current_frame = frame
        self.draw_frame = draw_frame

        # if not self.has_guessed:  # self.hough_result is None or len(self.hough_result) > self.max_line_num:
        #     print("before:", self.initial_guess)
        #     result = minimize(self.hough_pipeline, self.initial_guess, method='nelder-mead',
        #                       tol=2,
        #                       options={'disp': True}
        #                       )
        #     # print(self.initial_guess == result.x)
        #     self.initial_guess = result.x
        #     print("after:", self.initial_guess)
        #
        #     self.has_guessed = True
        # else:
        #     self.hough_pipeline(self.initial_guess)

        self.hough_pipeline(self.initial_guess)

        if self.hough_result is not None:
            # print("result length:", len(self.hough_result))
            # for rho, theta in self.hough_result[:, 0]:
            #     self.draw_houghlines(frame, rho, theta, (0, 0, 255))

            if len(self.hough_result) < self.num_clusters_k:
                num_clusters_k = len(self.hough_result)
            else:
                num_clusters_k = self.num_clusters_k
            _, label, clusters = cv2.kmeans(self.hough_result, num_clusters_k, None, self.k_means_criteria, 10,
                                            cv2.KMEANS_RANDOM_CENTERS)

            highest_scores = [0.0, 0.0, 0.0, 0.0]
            for rho, theta in clusters:
                self.compute_line_scores(rho, theta)

                score_info = max(self.scores, key=lambda line_score: line_score.score)
                line_index = self.scores.index(score_info)
                # print([line_score.score for line_score in self.scores])
                if score_info.score > self.min_score and score_info.score > highest_scores[line_index]:
                    highest_scores[line_index] = score_info.score
                    score_info.hough_coord = rho, theta

                    if line_index == 0:
                        score_info.color = (int(score_info.score * 255), 0, 0)
                    elif line_index == 1:
                        score_info.color = (0, int(score_info.score * 255), 0)
                    elif line_index == 2:
                        score_info.color = (0, 0, int(score_info.score * 255))

                        # color = (0, int(vert_score * 255), int(vert_score * 255))
                        # if vert_score > self.min_score:
                        #     vertical_lines.append((rho, theta, color))

            for index, score_info in enumerate(self.scores):
                if score_info.hough_coord is not None:
                    self.draw_houghline(self.draw_frame, score_info.hough_coord[0], score_info.hough_coord[1],
                                        score_info.color)
                    self.distances[index] = score_info.distance_value
                else:
                    self.distances[index] = None
                score_info.reset()

        self.logger.info("distances: %s" % self.distances)
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

        self.logger.info("function_result: %s" % function_result)
        self.pipeline_frame = dilation
        return function_result

    def convert_hough_coordinates(self, rho, theta):
        a = np.cos(theta)
        b = np.sin(theta)
        x0 = a * rho
        y0 = b * rho
        x1 = int(x0 + 1000 * -b)
        y1 = int(y0 + 1000 * a)
        x2 = int(x0 - 1000 * -b)
        y2 = int(y0 - 1000 * a)
        return x1, y1, x2, y2

    def draw_houghline(self, frame, rho, theta, color):
        x1, y1, x2, y2 = self.convert_hough_coordinates(rho, theta)
        cv2.line(frame, (x1, y1), (x2, y2), color, 2)

    def compute_line_scores(self, rho, theta):
        top_intercept = rho / np.cos(theta)
        angle = (np.pi / 2 + theta) % (2 * np.pi) - np.pi
        left_intercept = rho / np.cos(np.pi / 2 - theta)
        right_intercept = (self.width - top_intercept) * np.tan(angle)
        # if right_intercept > self.height:
        #     bottom_intercept = self.width - (right_intercept - self.height) / np.tan(angle)
        # else:
        #     bottom_intercept = self.width + (self.height - right_intercept) / np.tan(angle)

        self.left_score.compute_score(left_intercept)
        self.right_score.compute_score(right_intercept)

        if -self.height < right_intercept < 2 * self.height and -self.height < left_intercept < 2 * self.height:
            self.horz_score.compute_score(angle)
            self.horz_score.distance_value = (left_intercept + right_intercept) / 2

        self.left_score.distance_value = -top_intercept
        self.right_score.distance_value = top_intercept


class LineScore:
    def __init__(self, mean, std):
        self.mean = mean
        self.std = std
        self.normalized_value = norm.pdf(self.mean, self.mean, self.std)
        self.reset()

    def reset(self):
        self.score = 0.0
        self.hough_coord = None
        self.color = (0, 0, 0)
        self.distance_value = None

    def compute_score(self, value):
        self.score = norm.pdf(value, self.mean, self.std) / self.normalized_value


class VisualOdometer:
    def __init__(self, camera_matrix):
        self.camera_matrix = camera_matrix

        self.current_points = None
        self.prev_points = None

        self.current_frame = None
        self.prev_frame = None

        self.r_matrix = None
        self.t_matrix = None

        self.position = (0.0, 0.0, 0.0)
        self.rotation = (0.0, 0.0, 0.0)

        self.min_feature_num = 500
        self.feature_params = dict(
            maxCorners=2000,
            qualityLevel=0.001,
            minDistance=0.001,
            blockSize=3
        )
        self.lk_params = dict(
            winSize=(7, 7),
            maxLevel=2,
            criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03)
        )

        # self.orb = cv2.ORB_create(2000)

    def detect_features(self, frame):
        # keypoints = self.orb.detect(frame, None)
        # keypoints, descriptors = self.orb.compute(frame, keypoints)
        # return cv2.KeyPoint_convert(keypoints)
        points = cv2.goodFeaturesToTrack(frame, **self.feature_params)
        return points[:, 0]

    def track_features(self, prev_points, prev_frame, current_frame):
        current_points, status, error = \
            cv2.calcOpticalFlowPyrLK(prev_frame, current_frame, prev_points, None, **self.lk_params)

        new_current_points = np.array([])
        new_prev_points = np.array([])
        for index in range(len(status)):
            point = current_points[index]
            if point[0] < 0 or point[1] < 0:
                status[index][0] = 0
            if status[index][0] != 0:
                if len(new_current_points) == 0:
                    new_current_points = point
                    new_prev_points = prev_points[index]
                else:
                    new_current_points = np.vstack((new_current_points, point))
                    new_prev_points = np.vstack((new_prev_points, prev_points[index]))

        return new_current_points, new_prev_points

    def compute_pose(self, prev_points, current_points):
        E, mask = cv2.findEssentialMat(prev_points, current_points, self.camera_matrix,
                                       method=cv2.RANSAC, prob=0.999, threshold=3.0)
        points, rotation_matrix, translation_matrix, mask = \
            cv2.recoverPose(E, current_points, prev_points, self.camera_matrix)

        # print(rotation_matrix)
        # print(translation_matrix)
        # print()

        return rotation_matrix, translation_matrix

    def calculate_rotation(self, R):
        dist = np.sqrt(R[0, 0] ** 2 + R[1, 0] ** 2)
        if dist > 1E-6:
            roll = np.arctan2(R[2, 1], R[2, 2])
            pitch = np.arctan2(-R[2, 0], dist)
            yaw = np.arctan2(R[1, 0], R[0, 0])
        else:
            roll = np.arctan2(-R[1, 2], R[1, 1])
            pitch = np.arctan2(-R[2, 0], dist)
            yaw = 0.0

        return roll, pitch, yaw

    def update(self, frame, draw_frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if self.current_points is None:
            self.current_points = self.detect_features(frame)

            self.current_frame = frame
        else:
            self.prev_frame = self.current_frame
            self.current_frame = frame
            self.prev_points = self.current_points
            self.current_points, self.prev_points = \
                self.track_features(self.prev_points, self.prev_frame, self.current_frame)
            print(len(self.current_points))

            if len(self.prev_points) < self.min_feature_num:
                self.current_points = self.detect_features(frame)
            else:
                new_r, new_t = \
                    self.compute_pose(self.prev_points, self.current_points)
                if self.r_matrix is None or self.t_matrix is None:
                    self.r_matrix = new_r
                    self.t_matrix = new_t
                else:
                    scale = 1.0
                    if scale > 0.1 and new_t[2] > new_t[0] and new_t[2] > new_t[1]:
                        self.t_matrix += scale * np.dot(self.r_matrix, new_t)
                        self.r_matrix = np.dot(new_r, self.r_matrix)

                self.position = tuple(self.t_matrix.T[0].tolist())
                self.rotation = self.calculate_rotation(self.r_matrix)

                print("X: %s, Y: %s, R: %s" % (self.position[0], self.position[1], self.rotation[2]))

        for point in self.current_points:
            x, y = point
            cv2.circle(draw_frame, (int(x), int(y)), 3, (255, 0, 0))

        return draw_frame

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
