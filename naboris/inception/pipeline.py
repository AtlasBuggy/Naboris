import cv2
import time
import numpy as np
import multiprocessing
import tensorflow as tf

from naboris.texture.pipeline import TexturePipeline


class InceptionPipeline(TexturePipeline):
    def __init__(self, enabled=True, log_level=None):
        super(InceptionPipeline, self).__init__(enabled, log_level)

        self.model_path = "naboris/inception/output_graph.pb"
        self.labels_path = "naboris/inception/output_labels.txt"

        self.create_graph()

        num_threads = multiprocessing.cpu_count()
        print("Running on %s threads" % num_threads)
        self.sess = tf.Session(config=tf.ConfigProto(
            intra_op_parallelism_threads=num_threads))
        self.softmax_tensor = self.sess.graph.get_tensor_by_name('final_result:0')

        with open(self.labels_path) as labels_file:
            lines = labels_file.readlines()
            self.prediction_labels = [str(w).replace("\n", "") for w in lines]

    def create_graph(self):
        """Creates a graph from saved GraphDef file and returns a saver."""
        with tf.gfile.FastGFile(self.model_path, 'rb') as f:
            graph_def = tf.GraphDef()
            graph_def.ParseFromString(f.read())
            _ = tf.import_graph_def(graph_def, name='')

    def pipeline(self, frame):
        cropped = self.crop_frame(frame)

        t0 = time.time()
        predictions = self.sess.run(self.softmax_tensor,
                                    {'DecodeJpeg/contents:0': self.numpy_to_bytes(cropped)})
        predictions = np.squeeze(predictions)
        top_k = predictions.argsort()[::-1]
        answer = self.prediction_labels[top_k[0]]
        t1 = time.time()
        self.logger.info("Took: %0.4fs, Answer: %s" % (t1 - t0, answer))

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
