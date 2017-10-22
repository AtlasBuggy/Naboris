import os
import cv2
import json
import pickle
import numpy as np

from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV

from atlasbuggy.opencv import OpenCVPipeline, ImageMessage

from .localbinarypatterns import LocalBinaryPatterns


class TexturePipeline(OpenCVPipeline):
    def __init__(self, enabled=True, log_level=None):
        super(TexturePipeline, self).__init__(enabled, log_level)

        self.file_extension = ".jpg"
        self.database_file_path = "naboris/texture/training.json"
        self.model_pickle_path = "naboris/texture/models/texture.pkl"
        self.training_image_path = "naboris/texture/training_images"

        with open(self.database_file_path) as training_file:
            self.training_data = json.load(training_file)

        self.results_service_tag = "results"
        self.define_service(self.results_service_tag)

        self.texture_service_tag = "texture"
        self.define_service(self.texture_service_tag, ImageMessage)

        self.desc = LocalBinaryPatterns(24, 8)
        self.model = LinearSVC(C=500.0, random_state=20)
        self.classifier = CalibratedClassifierCV(self.model)
        self.load_model()

        self.cropped = None
        self.cropped_label = ""
        self.cropped_num = 0

        self.prediction_labels = sorted(list(self.training_data.keys()))

        self.offset = 100
        self.frame_num = 0

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
                if file_name.endswith(self.file_extension):
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

        image_dir = os.path.join(self.training_image_path, category)
        if not os.path.isdir(image_dir):
            os.mkdir(image_dir)

        path = os.path.join(image_dir, "%s-%s%s" % (category, count, self.file_extension))

        cv2.imwrite(path, image)
        self.logger.info("Wrote: %s" % path)

    def post_texture_images(self, data):
        frame, texture = data
        return frame.copy(), texture.copy()

    def get_crop_points(self, frame):
        height, width = frame.shape[0:2]
        y1 = height - self.offset * 2
        y2 = height

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

        max_index = np.argmax(prediction)
        prediction_label = self.prediction_labels[max_index]

        y1, y2, x1, x2 = self.get_crop_points(frame)
        # frame.setflags(write=1)
        # frame[y1: y2, x1: x2] = cv2.cvtColor(lbp, cv2.COLOR_GRAY2BGR)

        cv2.rectangle(frame, (x1 - 1, y1 - 1), (x2 + 1, y2 + 1), (255, 0, 0))

        self.broadcast_nowait((prediction_label, prediction[max_index]), self.results_service_tag)

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

        message = ImageMessage(self.cropped, self.frame_num)
        self.broadcast_nowait(message, self.texture_service_tag)

        self.frame_num += 1

        return frame

    def stop(self):
        with open(self.database_file_path, 'w+') as training_file:
            json.dump(self.training_data, training_file)
