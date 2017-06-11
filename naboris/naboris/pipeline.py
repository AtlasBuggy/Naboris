import os
import cv2
from skimage.segmentation import slic
from skimage.segmentation import mark_boundaries
import numpy as np

from atlasbuggy.cameras.cvpipeline import CvPipeline


class NaborisPipeline(CvPipeline):
    def __init__(self, enabled=True, log_level=None, generate_database=False):
        super(NaborisPipeline, self).__init__(enabled, log_level, generate_bytes=True)
        self.actuators = None
        self.autonomous_mode = False

        # self.orb = cv2.ORB_create()
        self.num_segments = 50
        self.kernel = np.ones((5, 5), np.uint8)
        self.generate_database = generate_database

        # directory = BaseFile.format_path_as_time("", None, "", "%Y_%b_%d %H;%M;%S", )[1]
        # self.database_dir = BaseFile("", directory, "", "", False, self.generate_bytes, False, False, False)
        # if self.generate_database:
        #     self.database_dir.make_dir()

    def take(self):
        self.capture = self.streams["capture"]
        # self.actuators = self.streams["actuators"]

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
        #

        return self.over_segment(frame)
        # return frame

    def over_segment(self, frame):
        erosion = cv2.erode(frame, self.kernel, iterations=2)
        segments = slic(erosion, n_segments=self.num_segments, sigma=5)

        if self.generate_database:
            file_name = "%s-x.png" % self.capture.current_frame
            full_path = os.path.join(self.database_dir.directory, file_name)
            cv2.imwrite(full_path, frame)

            for (i, seg_value) in enumerate(np.unique(segments)):
                mask = np.zeros(frame.shape[:2], dtype=np.uint8)
                mask[segments == seg_value] = 255

                alpha_channel = np.ones(mask.shape, dtype=np.uint8)
                alpha_channel = cv2.bitwise_and(alpha_channel, alpha_channel, mask=mask) * 255

                b_channel, g_channel, r_channel = cv2.split(frame)
                frame_rgba = cv2.merge((b_channel, g_channel, r_channel, alpha_channel))

                file_name = "%s-%s.png" % (self.capture.current_frame, i)
                full_path = os.path.join(self.database_dir.directory, file_name)
                cv2.imwrite(full_path, frame_rgba)

        return mark_boundaries(frame, segments)

    def orb(self, frame):
        kp = self.orb.detect(frame, None)
        kp, des = self.orb.compute(frame, kp)
        return cv2.drawKeypoints(frame, kp, None, color=(128, 255, 0), flags=0)

    def hough_detector(self, input_frame):
        blur = cv2.cvtColor(input_frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.equalizeHist(blur)
        blur = cv2.GaussianBlur(blur, (11, 11), 0)

        frame = cv2.Canny(blur, 1, 100)
        lines = cv2.HoughLines(
            frame, rho=1.2, theta=np.pi / 180,
            threshold=125,
            # min_theta=60 * np.pi / 180,
            # max_theta=120 * np.pi / 180
        )
        # blur = cv2.putText(blur, str(self.capture.current_frame), (30, 30), cv2.FONT_HERSHEY_PLAIN, 1, (255, 128, 0))
        # safety_percentage, line_angle = self.draw_lines(input_frame, lines)

        # if lines is not None and self.autonomous_mode:
        #     self.actuators.set_all_leds(len(lines) * 10, 0, 0)

        # output_frame = cv2.add(cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR), input_frame)
        # output_frame = np.concatenate((output_frame, cv2.cvtColor(blur, cv2.COLOR_GRAY2BGR)), axis=1)
        return blur  # , lines, safety_percentage, line_angle

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
