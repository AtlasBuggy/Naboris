import cv2
import scipy.misc
import numpy as np
import tensorflow as tf

from atlasbuggy.camera.pipeline import Pipeline
from atlasbuggy.subscriptions import *

from .model import monodepth_parameters, MonodepthModel


def post_process_disparity(disp):
    _, h, w = disp.shape
    l_disp = disp[0, :, :]
    r_disp = np.fliplr(disp[1, :, :])
    m_disp = 0.5 * (l_disp + r_disp)
    l, _ = np.meshgrid(np.linspace(0, 1, w), np.linspace(0, 1, h))
    l_mask = 1.0 - np.clip(20 * (l - 0.05), 0, 1)
    r_mask = np.fliplr(l_mask)
    return r_mask * l_disp + l_mask * r_disp + (1.0 - l_mask - r_mask) * m_disp


class MonodepthPipeline(Pipeline):
    def __init__(self, model_name, enabled=True, log_level=None):
        super(MonodepthPipeline, self).__init__(enabled, log_level)

        self.results_service_tag = "results"
        self.add_service(self.results_service_tag, lambda data: data)

        self.viewer_tag = "viewer"
        self.viewer_feed = None
        self.require_subscription(self.viewer_tag, Update)

        model_dir = "depth_models/monodepth/model_" + model_name

        if model_name.endswith("resnet"):
            encoder = "resnet50"
        else:
            encoder = "vgg"

        self.input_height = 256
        self.input_width = 512

        params = monodepth_parameters(
            encoder=encoder,
            height=self.input_height,
            width=self.input_width,
            batch_size=2,
            num_threads=1,
            num_epochs=1,
            do_stereo=False,
            wrap_mode="border",
            use_deconv=False,
            alpha_image_loss=0,
            disp_gradient_loss_weight=0,
            lr_loss_weight=0,
            full_summary=False
        )

        self.left = tf.placeholder(tf.float32, [2, self.input_height, self.input_width, 3])
        self.model = MonodepthModel(params, "test", self.left, None)

        config = tf.ConfigProto(allow_soft_placement=True)
        self.sess = tf.Session(config=config)

        # SAVER
        train_saver = tf.train.Saver()

        # INIT
        self.sess.run(tf.global_variables_initializer())
        self.sess.run(tf.local_variables_initializer())
        coordinator = tf.train.Coordinator()
        tf.train.start_queue_runners(sess=self.sess, coord=coordinator)

        # RESTORE
        train_saver.restore(self.sess, model_dir)

    def take_from_pipeline(self, subscriptions):
        self.viewer_feed = subscriptions[self.viewer_tag].get_feed()

    def fit_frame(self, input_image):
        original_height, original_width, num_channels = input_image.shape
        if num_channels == 4:
            input_image = input_image[:, :, :3]
        elif num_channels == 1:
            input_image = np.tile((input_image, input_image, input_image), 2)
        input_image = scipy.misc.imresize(input_image, [self.input_height, self.input_width], interp='lanczos')
        input_image = input_image.astype(np.float32) / 255
        fitted_frame = np.stack((input_image, np.fliplr(input_image)), 0)
        return fitted_frame

    def pipeline(self, frame):
        fitted_frame = self.fit_frame(frame)

        disp = self.sess.run(self.model.disp_left_est[0], feed_dict={self.left: fitted_frame})
        disp_pp = post_process_disparity(disp.squeeze()).astype(np.float32)

        depth_image = scipy.misc.imresize(disp_pp.squeeze(), (self.height, self.width))

        # depth_values = cv2.resize(disp_pp.squeeze(), (self.width, self.height))
        # print((np.max(depth_values), np.min(depth_values)), (np.max(depth_values), np.min(depth_values)))

        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(depth_image)

        depth_image = cv2.cvtColor(depth_image, cv2.COLOR_GRAY2BGR)

        cv2.circle(depth_image, min_loc, 5, (0, 255, 0))
        cv2.circle(depth_image, max_loc, 5, (0, 0, 255))

        # self.post(disp, self.results_service_tag)
        offset = 50
        pt1 = (self.width // 2 - offset, self.height // 2 - offset)
        pt2 = (self.width // 2 + offset, self.height // 2 + offset)
        cv2.rectangle(depth_image, pt1, pt2, (255, 0, 0))

        # print(np.average(disp_pp[self.height // 2 - offset: self.height // 2 + offset,
        #                  self.width // 2 - offset: self.width // 2 + offset]))
        while not self.viewer_feed.empty():
            event, x, y, flags, param = self.viewer_feed.get()
            if 0 <= x < self.width and 0 <= y < self.height:
                print("(%s, %s) -> %s" % (x, y, depth_image[y, x]))

                # cv2.circle(depth_image, (x, y), 1, (0, 255, 0))
                # cv2.circle(depth_image, (y, x), 1, (0, 0, 255))

        return np.concatenate((depth_image, frame), axis=1)

    def stop(self):
        if self.sess is not None:
            self.logger.debug('Close interactive session')
            self.sess.close()
