
import cv2
import time
import numpy as np
from atlasbuggy.camerastream.cvpipeline import CvPipeline


class NaborisPipeline(CvPipeline):
    def __init__(self, capture, actuators, enabled=True, debug=False):
        super(NaborisPipeline, self).__init__(capture, enabled, debug, generate_bytes=True)
        self.actuators = actuators
        self.autonomous_mode = False

    def pipeline(self, input_frame):
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
        blur = cv2.putText(blur, str(self.capture.current_frame), (30, 30), cv2.FONT_HERSHEY_PLAIN, 1, (255, 128, 0))
        # safety_percentage, line_angle = self.draw_lines(input_frame, lines)

        if lines is not None and self.autonomous_mode:
            self.actuators.set_all_leds(len(lines) * 10, 0, 0)

        # output_frame = cv2.add(cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR), input_frame)
        # output_frame = np.concatenate((output_frame, cv2.cvtColor(blur, cv2.COLOR_GRAY2BGR)), axis=1)
        return blur #, lines, safety_percentage, line_angle

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
