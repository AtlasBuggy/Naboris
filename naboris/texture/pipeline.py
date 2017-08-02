import os
import re
import cv2
import json
import pickle
import numpy as np

from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV

from atlasbuggy.camera.pipeline import Pipeline

from .localbinarypatterns import LocalBinaryPatterns


class TexturePipeline(Pipeline):
    def __init__(self, enabled=True, log_level=None):
        super(TexturePipeline, self).__init__(enabled, log_level)

        self.database_file_path = "naboris/texture/training.json"
        self.model_pickle_path = "naboris/texture/models/texture.pkl"
        self.training_image_path = "naboris/texture/training_images"

        with open(self.database_file_path) as training_file:
            self.training_data = json.load(training_file)

        self.results_service_tag = "results"
        self.add_service(self.results_service_tag, lambda data: data)

        self.texture_service_tag = "texture"
        self.add_service(self.texture_service_tag, self.post_texture_images)

        self.desc = LocalBinaryPatterns(24, 8)
        self.model = LinearSVC(C=500.0, random_state=20)
        self.classifier = CalibratedClassifierCV(self.model)
        self.load_model()

        self.cropped = None
        self.cropped_label = ""
        self.cropped_num = 0

        self.prediction_labels = sorted(list(self.training_data.keys()))

        self.height_offset = 100
        self.offset = 100

    def load_model(self):
        with open(self.model_pickle_path, 'rb') as model:
            self.classifier = pickle.load(model)

    def train(self):
        labels = []
        data = []

        for label, num_images in self.training_data.items():
            print("loading '%s'. %s images" % (label, num_images))
            dir_path = os.path.join(self.training_image_path, label)
            file_names = os.listdir(dir_path)
            if len(file_names) != num_images:
                self.logger.warning(
                    "Number of images (%s) doesn't match number in json (%s)" % (len(file_names), num_images)
                )

            for file_name in file_names:
                if file_name.endswith(".png"):
                    path = os.path.join(dir_path, file_name)

                    if not os.path.isfile(path):
                        raise FileNotFoundError(path)
                    labels.append(label)
                    image = cv2.imread(path)
                    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                    gray = cv2.equalizeHist(gray)
                    hist, _ = self.desc.describe(gray)
                    data.append(hist)
            print("done")

        print("fitting...")
        self.classifier.fit(data, labels)
        print("done")
        with open("naboris/texture/models/texture.pkl", 'wb') as model:
            pickle.dump(self.classifier, model)

    def write_training_image(self, category, image):
        self.training_data[category] += 1
        count = self.training_data[category]

        path = os.path.join(self.training_image_path, category, "%s-%s.png" % (category, count))

        cv2.imwrite(path, image)
        self.logger.info("Wrote: %s" % path)

    def post_texture_images(self, data):
        frame, texture = data
        return frame.copy(), texture.copy()

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

        # lbp = np.uint8(lbp)
        # lbp = cv2.equalizeHist(lbp)
        prediction = self.classifier.predict_proba(hist.reshape(1, -1))
        prediction = prediction.squeeze()

        index = np.argmax(prediction)
        prediction_label = self.prediction_labels[index]

        y1, y2, x1, x2 = self.get_crop_points(frame)
        # frame.setflags(write=1)
        # frame[y1: y2, x1: x2] = cv2.cvtColor(lbp, cv2.COLOR_GRAY2BGR)

        cv2.rectangle(frame, (x1 - 1, y1 - 1), (x2 + 1, y2 + 1), (255, 0, 0))

        text_y = 30
        num_line_elements = 3
        for index in range(0, len(prediction), num_line_elements):
            line_predictions = prediction[index: index + num_line_elements]
            line_map = map(lambda value: "%0.3f" % (100 * value), line_predictions)
            predictions_string = ", ".join(line_map)

            if index < num_line_elements:
                line = "%s %s" % (prediction_label, predictions_string)
            else:
                line = predictions_string

            cv2.putText(frame, line, (10, text_y), cv2.FONT_HERSHEY_SIMPLEX,
                        0.75, (0, 0, 255), 2)
            text_y += 25

        self.post((prediction_label, prediction[index]), self.results_service_tag)
        self.post((frame, self.cropped), self.texture_service_tag)

        return frame

    def stop(self):
        with open(self.database_file_path, 'w+') as training_file:
            json.dump(self.training_data, training_file)
