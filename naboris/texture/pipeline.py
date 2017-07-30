import os
import cv2
import numpy as np

from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV

from atlasbuggy.camera.pipeline import Pipeline
from atlasbuggy.subscriptions import *

from .localbinarypatterns import LocalBinaryPatterns


class TexturePipeline(Pipeline):
    def __init__(self, training_image_dir, enabled=True, log_level=None):
        super(TexturePipeline, self).__init__(enabled, log_level)

        self.results_service_tag = "results"
        self.add_service(self.results_service_tag, lambda data: data)

        self.viewer_tag = "viewer"
        self.viewer_feed = None
        self.require_subscription(self.viewer_tag, Update)

        self.desc = LocalBinaryPatterns(8, 2)
        self.model = LinearSVC(C=500.0, random_state=20)
        self.classifier = CalibratedClassifierCV(self.model)

        self.cropped = None
        self.cropped_label = ""
        self.cropped_num = 0

        self.labels = []
        self.data = []
        self.prediction_labels = []

        for label in os.listdir(training_image_dir):
            label_dir = os.path.join(training_image_dir, label)
            if os.path.isdir(label_dir):
                self.prediction_labels.append(label)

                for image_name in os.listdir(label_dir):
                    if image_name.endswith(".png"):
                        self.labels.append(label)

                        path = os.path.join(label_dir, image_name)
                        image = cv2.imread(path)
                        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                        hist, _ = self.desc.describe(gray)
                        self.data.append(hist)

        self.classifier.fit(self.data, self.labels)

        self.height_offset = 100
        self.offset = 50

    def get_crop_points(self, frame):
        height, width = frame.shape[0:2]
        y1 = height // 2 - self.offset + self.height_offset
        y2 = height // 2 + self.offset + self.height_offset

        x1 = width // 2 - self.offset
        x2 = width // 2 + self.offset

        return y1, y2, x1, x2

    def crop_frame(self, frame):
        y1, y2, x1, x2 = self.get_crop_points(frame)
        return frame[y1: y2, x1: x2]

    def pipeline(self, frame):
        self.cropped = self.crop_frame(frame)
        gray = cv2.cvtColor(self.cropped, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        hist, lbp = self.desc.describe(gray)

        lbp = np.uint8(lbp)
        lbp = cv2.equalizeHist(lbp)
        prediction = self.classifier.predict_proba(hist.reshape(1, -1))

        index = np.argmax(prediction.squeeze())
        prediction = self.prediction_labels[index]

        y1, y2, x1, x2 = self.get_crop_points(frame)
        frame[y1: y2, x1: x2] = cv2.cvtColor(lbp, cv2.COLOR_GRAY2BGR)

        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0))

        cv2.putText(frame, prediction, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                    1.0, (0, 0, 255), 3)

        return frame

    def change_label(self, index):
        if 0 <= index < len(self.prediction_labels):
            self.cropped_label = self.prediction_labels[index]
            print(self.cropped_label)

    def save_image(self):
        self.cropped_num += 1
        cv2.imwrite("%s_%s.png" % (self.cropped_label, self.cropped_num), self.cropped)
