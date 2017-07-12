import cv2
from scipy import ndimage
from skimage.feature import peak_local_max
from skimage.morphology import watershed
import numpy as np

from atlasbuggy.cameras.cvpipeline import CvPipeline


class NaborisPipeline(CvPipeline):
    def __init__(self, enabled=True, log_level=None):
        super(NaborisPipeline, self).__init__(enabled, log_level)

    def pipeline(self, frame):
        return self.hough_detector(frame)

    def hough_detector(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.medianBlur(gray, 5)
        laplacian_64f = cv2.Laplacian(gray, cv2.CV_64F, ksize=5, scale=0.5)
        abs_laplacian_64f = np.absolute(laplacian_64f)
        laplacian_8u = np.uint8(abs_laplacian_64f)

        mask = cv2.inRange(laplacian_8u, 80, 255)
        masked = cv2.bitwise_and(laplacian_8u, laplacian_8u, mask=mask)

        kernel = np.ones((5, 5), np.uint8)
        dilated = cv2.dilate(masked, kernel, iterations=1)

        canny = cv2.Canny(dilated, 1, 100)

        # lines = cv2.HoughLines(canny, rho=1.0, theta=np.pi / 180, threshold=125)
        # if lines is not None:
        #     for rho, theta in lines[:, 0]:
        #         a = np.cos(theta)
        #         b = np.sin(theta)
        #         x0 = a * rho
        #         y0 = b * rho
        #         x1 = int(x0 + 1000 * (-b))
        #         y1 = int(y0 + 1000 * (a))
        #         x2 = int(x0 - 1000 * (-b))
        #         y2 = int(y0 - 1000 * (a))
        #
        #         cv2.line(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)

        lines = cv2.HoughLinesP(canny, 1, np.pi / 180, 100, minLineLength=100, maxLineGap=10)
        if lines is not None:
            for x1, y1, x2, y2 in lines[:, 0]:
                cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        return np.concatenate((frame, cv2.cvtColor(canny, cv2.COLOR_GRAY2BGR)), axis=1)

        # sobelx64f = cv2.Sobel(frame, cv2.CV_64F, 1, 0, ksize=3)
        # abs_sobel64f = np.absolute(sobelx64f)
        # sobel_8u = np.uint8(abs_sobel64f)
        # gray_1 = cv2.cvtColor(sobel_8u, cv2.COLOR_BGR2GRAY)
        #
        # sobelx64f = cv2.Sobel(frame, cv2.CV_64F, 0, 1, ksize=3)
        # abs_sobel64f = np.absolute(sobelx64f)
        # sobel_8u = np.uint8(abs_sobel64f)
        # gray_2 = cv2.cvtColor(sobel_8u, cv2.COLOR_BGR2GRAY)
        # gray = cv2.medianBlur(gray_1 + gray_2, 5)

        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        kernel = np.ones((3, 3), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)

        return thresh


        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        # thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 5, 2)


        # return thresh

        # blur = cv2.cvtColor(input_frame.copy(), cv2.COLOR_BGR2GRAY)
        # blur = cv2.equalizeHist(blur)
        # blur = cv2.GaussianBlur(blur, (11, 11), 0)

        canny = cv2.Canny(thresh, 1, 100)
        lines = cv2.HoughLines(
            canny, rho=1.0, theta=np.pi / 180,
            threshold=125,
            # min_theta=60 * np.pi / 180,
            # max_theta=120 * np.pi / 180
        )
        # blur = cv2.putText(blur, str(self.capture.current_frame), (30, 30), cv2.FONT_HERSHEY_PLAIN, 1, (255, 128, 0))
        self.draw_lines(input_frame, lines)

        # if lines is not None and self.autonomous_mode:
        #     self.actuators.set_all_leds(len(lines) * 10, 0, 0)

        # output_frame = cv2.add(cv2.cvtColor(blur, cv2.COLOR_GRAY2BGR), input_frame)
        output_frame = np.concatenate((input_frame, cv2.cvtColor(canny, cv2.COLOR_GRAY2BGR)), axis=1)
        return output_frame  # , lines, safety_percentage, line_angle

    def draw_lines(self, frame, lines, draw_threshold=30):
        height, width = frame.shape[0:2]

        if lines is not None:
            counter = 0
            largest_y = 0
            left_y = 0
            right_y = 0
            largest_coords = None

            for line in lines:
                rho, theta = line[0][0], line[0][1]
                a = np.cos(theta)
                b = np.sin(theta)
                x0 = a * rho
                y0 = b * rho

                x1 = int(x0 + 1000 * -b)
                y1 = int(y0 + 1000 * a)
                x2 = int(x0 - 1000 * -b)
                y2 = int(y0 - 1000 * a)

                y3 = int(y0 - width / 2 * a)

                # if y2 > largest_y:
                #     largest_y = y2
                #     largest_coords = (x1, y1), (x2, y2)
                if y3 > largest_y:
                    largest_y = y3
                    largest_coords = x1, y1, x2, y2
                    left_y = y0
                    right_y = int(y0 - width * a)

                cv2.line(frame, (x1, y1), (x2, y2), (150, 150, 150), 2)
                # cv2.circle(frame, (x0, y0), 10, (150, 255, 50), 2)
                counter += 1
                if counter > draw_threshold:
                    break

            if largest_coords is not None:
                x1, y1, x2, y2 = largest_coords
                cv2.line(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                line_angle = np.arctan2(y1 - y2, x1 - x2)
                if line_angle < 0:
                    line_angle += 2 * np.pi
                line_angle -= np.pi
                line_angle *= -1
            else:
                line_angle = 0.0

            if left_y > right_y:
                safety_value = left_y / height
            else:
                safety_value = right_y / height

            if safety_value > 1.0:
                safety_value = 1.0
            if safety_value < 0.0:
                safety_value = 0.0
            # print("%0.4f, %0.4f" % (safety_value, line_angle))
            # time.sleep(0.01)
            return safety_value, line_angle
            # return largest_y / height
        return 0.0, 0.0
