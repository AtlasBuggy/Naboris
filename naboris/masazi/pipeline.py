import cv2
import numpy as np
import tensorflow as tf
from atlasbuggy.camera.pipeline import Pipeline

from .model import inference, inference_refine


class MasazIDepthPipeline(Pipeline):
    def __init__(self, course_model_dir, refine_model_dir, enabled=True, log_level=None):
        super(MasazIDepthPipeline, self).__init__(enabled, log_level)

        # expected size of inputs and outputs
        self.model_image_height = 228
        self.model_image_width = 304
        self.output_height = 55
        self.output_width = 74
        self.resize_height = self.output_height  # * 3
        self.resize_width = self.output_width  # * 3

        self.results_service_tag = "results"
        self.add_service(self.results_service_tag, lambda data: data)

        # tensorflow graph that represents the sequence of operations to run
        self.graph = tf.Graph()

        self.keep_conv = tf.placeholder(tf.float32)
        self.keep_hidden = tf.placeholder(tf.float32)

        # define image placeholder variable to inject into the graph
        # shape=(number of images in a batch, height, width, number of channels (BGR))
        self.input_name = "input"
        images = tf.placeholder(tf.float32, shape=(1, self.model_image_height, self.model_image_width, 3),
                                name=self.input_name)

        # instantiate coarse model placeholder
        coarse = inference(images, self.keep_conv, trainable=False)

        # instantiate fine model placeholder. The output (logits) is the depth image
        self.logits = inference_refine(images, coarse, self.keep_conv, self.keep_hidden)

        # create a tf session
        self.sess = tf.Session(config=tf.ConfigProto(log_device_placement=False))

        # create coarse and fine parameter placeholder variables
        coarse_params = {}
        refine_params = {}
        for variable in tf.global_variables():
            variable_name = variable.name
            # self.logger.debug(("parameter: %s" % (variable_name)))
            if variable_name.find("/") < 0 or variable_name.count("/") != 1:
                continue
            if variable_name.find('coarse') >= 0:
                coarse_params[variable_name] = variable
            # self.logger.debug(("parameter: %s" % (variable_name)))
            if variable_name.find('fine') >= 0:
                refine_params[variable_name] = variable

        # instantiate model recovery objects
        saver_coarse = tf.train.Saver(coarse_params)
        saver_refine = tf.train.Saver(refine_params)

        # restore coarse model
        coarse_ckpt = tf.train.get_checkpoint_state(course_model_dir)
        saver_coarse.restore(self.sess, coarse_ckpt.model_checkpoint_path)

        # restore fine model
        refine_ckpt = tf.train.get_checkpoint_state(refine_model_dir)
        saver_refine.restore(self.sess, refine_ckpt.model_checkpoint_path)

    def pipeline(self, frame):
        # resize image to the expected input
        image_tensor = cv2.resize(frame, (self.model_image_width, self.model_image_height))
        image_tensor = np.expand_dims(image_tensor, 0)

        # run the model on the current image and return the depth output
        logits_val = self.sess.run(
            self.logits,
            feed_dict={self.keep_conv        : 0.8,
                       self.keep_hidden      : 0.5,
                       self.input_name + ":0": image_tensor}
        )

        # generate and post the depth image to streams subscribed to the results service.
        # Return depth map as the pipeline output
        depth_image = self.generate_result(logits_val)

        # embed depth image in the top left corner of the original image
        depth_image = cv2.equalizeHist(depth_image)
        depth_image = cv2.cvtColor(depth_image, cv2.COLOR_GRAY2BGR)
        depth_image = cv2.resize(depth_image, (self.resize_width, self.resize_height))
        frame = cv2.resize(frame, (self.model_image_width, self.model_image_height))
        frame[0:self.resize_height, 0:self.resize_width] = depth_image

        return frame

    def generate_result(self, logits_val):
        # reshape array into 2D
        depth = logits_val[0].transpose(2, 0, 1)

        # adjust the values of the depth image to be from 0...255
        if np.max(depth) != 0:
            depth_image = (depth / np.max(depth)) * 255.0
        else:
            depth_image = depth * 255.0

        # post depth information to subscribers
        self.post(logits_val[0], self.results_service_tag)

        # convert depth image to correct data type
        depth_image = np.uint8(depth_image[0])
        return depth_image
