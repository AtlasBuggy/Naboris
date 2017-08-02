import cv2
import numpy as np
import tensorflow as tf

from atlasbuggy.camera.pipeline import Pipeline


class InceptionPipeline(Pipeline):
    def __init__(self, enabled=True, log_level=None):
        super(InceptionPipeline, self).__init__(enabled, log_level)

        self.results_service_tag = "results"
        self.add_service(self.results_service_tag)

        self.texture_service_tag = "texture"
        self.add_service(self.texture_service_tag, self.post_texture_images)

        self.model_path = "naboris/inception/output_graph.pb"
        self.labels_path = "naboris/inception/output_labels.txt"

        self.offset = 100

        self.create_graph()

        self.sess = tf.Session()
        self.softmax_tensor = self.sess.graph.get_tensor_by_name('final_result:0')

        with open(self.labels_path) as labels_file:
            lines = labels_file.readlines()
            self.prediction_labels = [str(w).replace("\n", "") for w in lines]

    def post_texture_images(self, data):
        frame, texture = data
        return frame.copy(), texture.copy()

    def create_graph(self):
        """Creates a graph from saved GraphDef file and returns a saver."""
        # Creates graph from saved graph_def.pb.
        with tf.gfile.FastGFile(self.model_path, 'rb') as f:
            graph_def = tf.GraphDef()
            graph_def.ParseFromString(f.read())
            _ = tf.import_graph_def(graph_def, name='')

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
        cropped = self.crop_frame(frame)

        predictions = self.sess.run(self.softmax_tensor,
                                    {'DecodeJpeg/contents:0': self.numpy_to_bytes(cropped)})
        predictions = np.squeeze(predictions)
        top_k = predictions.argsort()[::-1]
        answer = self.prediction_labels[top_k[0]]

        cv2.putText(frame, answer, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                    0.75, (0, 0, 255), 2)

        y1, y2, x1, x2 = self.get_crop_points(frame)
        cv2.rectangle(frame, (x1 - 1, y1 - 1), (x2 + 1, y2 + 1), (255, 0, 0))

        self.post((answer, top_k[0]), self.results_service_tag)
        self.post((frame, cropped), self.texture_service_tag)

        return frame

    @staticmethod
    def numpy_to_bytes(frame):
        return cv2.imencode(".jpg", frame)[1].tostring()

    def stop(self):
        self.sess.close()
