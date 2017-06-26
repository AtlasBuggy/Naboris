import cv2
from scipy import ndimage
from skimage.feature import peak_local_max
from skimage.morphology import watershed
import numpy as np

from atlasbuggy.cameras.cvpipeline import CvPipeline


class NaborisPipeline(CvPipeline):
    def __init__(self, enabled=True, log_level=None):
        super(NaborisPipeline, self).__init__(enabled, log_level)
        self.actuators = None
        self.autonomous_mode = False

        self.orb = cv2.ORB_create()

    def pipeline(self, frame):
        # over segment
        # join with classifier
        # hough line fit boundaries
        # use vertical regions as basis for ground 3D orientation (use camera parameters)

        # -- Make3D --
        # over segment
        # compute segment features: position, color, response magnitude, kurtosis texture, region shape
        # Split image into 11 segments
        # Use surrounding neighbors and linear predictor to predict 3D position of superpixel
        # Use linear logistic regression to compute the confidence of these predictions
        # Perform global inference using local constraints

        # -- room as a box --
        # use line segments to reconstruct room

        # return self.compute_orb(frame)
        return self.hough_detector(frame)
        # return self.watershed(frame)

    def watershed(self, frame):
        # shifted = cv2.pyrMeanShiftFiltering(frame, 21, 51)
        shifted = cv2.medianBlur(frame, 21)
        gray = cv2.cvtColor(shifted, cv2.COLOR_BGR2GRAY)
        # thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH)[1]
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 11, 2)

        D = ndimage.distance_transform_edt(thresh)
        local_max = peak_local_max(D, indices=False, min_distance=20, labels=thresh)

        markers = ndimage.label(local_max, structure=np.ones((3, 3)))[0]
        labels = watershed(-D, markers, mask=thresh)

        for label in np.unique(labels):
            # if the label is zero, we are examining the 'background'
            # so simply ignore it
            if label == 0:
                continue

            # otherwise, allocate memory for the label region and draw
            # it on the mask
            mask = np.zeros(gray.shape, dtype="uint8")
            mask[labels == label] = 255

            # detect contours in the mask and grab the largest one
            cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
                                    cv2.CHAIN_APPROX_SIMPLE)[-2]

            frame = cv2.drawContours(frame, cnts, -1, (0, 0, 255), 3)
            # c = max(cnts, key=cv2.contourArea)
            #
            # # draw a circle enclosing the object
            # ((x, y), r) = cv2.minEnclosingCircle(c)
            # cv2.circle(frame, (int(x), int(y)), int(r), (0, 255, 0), 2)
            # cv2.putText(frame, "#{}".format(label), (int(x) - 10, int(y)),
            #             cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        return frame

    def compute_orb(self, frame):
        kp = self.orb.detect(frame, None)
        kp, des = self.orb.compute(frame, kp)
        return cv2.drawKeypoints(frame, kp, None, color=(128, 255, 0), flags=0)

    def hough_detector(self, input_frame):
        shifted = cv2.medianBlur(input_frame, 11)
        gray = cv2.cvtColor(shifted, cv2.COLOR_BGR2GRAY)
        # thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH)[1]
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 11, 2)

        kernel = np.ones((3, 3), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
        # return thresh

        # blur = cv2.cvtColor(input_frame.copy(), cv2.COLOR_BGR2GRAY)
        # blur = cv2.equalizeHist(blur)
        # blur = cv2.GaussianBlur(blur, (11, 11), 0)

        blur = cv2.Canny(thresh, 1, 100)
        lines = cv2.HoughLines(
            blur, rho=1.2, theta=np.pi / 180,
            threshold=125,
            # min_theta=60 * np.pi / 180,
            # max_theta=120 * np.pi / 180
        )
        # blur = cv2.putText(blur, str(self.capture.current_frame), (30, 30), cv2.FONT_HERSHEY_PLAIN, 1, (255, 128, 0))
        self.draw_lines(input_frame, lines)

        # if lines is not None and self.autonomous_mode:
        #     self.actuators.set_all_leds(len(lines) * 10, 0, 0)

        # output_frame = cv2.add(cv2.cvtColor(blur, cv2.COLOR_GRAY2BGR), input_frame)
        output_frame = np.concatenate((input_frame, cv2.cvtColor(blur, cv2.COLOR_GRAY2BGR)), axis=1)
        return output_frame  # , lines, safety_percentage, line_angle
        # return blur

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
