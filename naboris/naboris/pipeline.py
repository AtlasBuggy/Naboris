import cv2
# from scipy import ndimage
# from skimage.feature import peak_local_max
# from skimage.morphology import watershed
import numpy as np
from numpy import linalg

from atlasbuggy.camera.pipeline import Pipeline


class NaborisPipeline(Pipeline):
    def __init__(self, enabled=True, log_level=None):
        super(NaborisPipeline, self).__init__(enabled, log_level)

        self.left_distance = 0
        self.right_distance = 0
        self.forward_distance = 0

        self.skelton_kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
        self.morph_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))

        self.k_means_criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        self.num_clusters_k = 3

        self.results_service_tag = "results"
        self.add_service(self.results_service_tag, self.results_post_service)

    def results_post_service(self, data):
        return data

    def pipeline(self, frame):
        # height, width = frame.shape[0:2]
        # new_height = height // 3
        # new_width = width // 6
        # center_x = width // 2
        # # center_y = height // 2
        #
        # frame = frame[height - new_height:  height, center_x - new_width: center_x + new_width]

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (9, 9), 0)
        laplacian_64f = cv2.Laplacian(gray, cv2.CV_16S, ksize=3, scale=1.5, delta=0)
        abs_laplacian_64f = np.absolute(laplacian_64f)
        laplacian_8u = np.uint8(abs_laplacian_64f)
        value, diff_frame = cv2.threshold(laplacian_8u, 10, 255, cv2.THRESH_BINARY)

        # erosion = cv2.erode(dilation, self.morph_kernel, iterations=1)
        opening = cv2.morphologyEx(diff_frame, cv2.MORPH_OPEN, self.morph_kernel, iterations=1)
        dilation = cv2.dilate(opening, self.morph_kernel, iterations=1)

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

        canny = cv2.Canny(dilation, 1, 100)

        lines = cv2.HoughLines(canny, rho=1.5, theta=np.pi / 180, threshold=125)

        if lines is not None:
            for rho, theta in lines[:, 0]:
                self.draw_houghlines(frame, rho, theta, (0, 0, 255))

            if len(lines) > self.num_clusters_k:
                ret, label, center = cv2.kmeans(lines, self.num_clusters_k, None, self.k_means_criteria, 10, cv2.KMEANS_RANDOM_CENTERS)

                for pt in center:
                    print(pt[1], end=", ")
                    self.draw_houghlines(frame, pt[0], pt[1], (0, 255, 255))
                print()

                # self.post((cluster1, cluster2, center), self.results_service_tag)

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

        return np.concatenate((frame, cv2.cvtColor(canny, cv2.COLOR_GRAY2BGR)), axis=1)

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

    @staticmethod
    def least_squares_intersection(a, n, transpose=True):
        """
        Return the point of intersection computed using the least-square method.
        :param a: a list of point lying on the lines. Points are nx1 matrices
        :param n: a list of line directions. Directions are nx1 matrices.
        :param transpose: should transpose vectors? default true
        :return: the point of intersection
        """
        assert (len(a) == len(n))  # same numbers of points as numbers of directions

        if transpose:
            n = map(lambda v: np.asmatrix(v / linalg.norm(v)).T, n)  # normalize directions and transpose
            a = map(lambda v: np.asmatrix(v).T, a)  # transform into matrix and transpose
        else:
            n = map(lambda v: np.asmatrix(v / linalg.norm(v)).T, n)  # normalize directions
            a = map(lambda v: np.asmatrix(v), a)  # transform into matrix

        n_0 = next(n)
        r = np.zeros((n_0.shape[0], n_0.shape[0]))
        q = np.zeros((n_0.shape[0], 1))
        for point, direction in zip(a, n):
            ri = np.identity(direction.shape[0]) - direction.dot(direction.T)
            qi = ri.dot(point)
            r = r + ri
            q = q + qi

        return linalg.solve(r, q)
