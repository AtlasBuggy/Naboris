import numpy as np

from atlasbuggy import Message
from atlasbuggy.opencv import OpenCVPipeline

from orbslam2 import *


class OrbslamMessage(Message):
    def __init__(self, n, state, x=None, y=None, z=None, qw=None, qx=None, qy=None, qz=None, timestamp=None):
        super(OrbslamMessage, self).__init__(timestamp, n)

        # position
        self.x = x
        self.y = y
        self.z = z

        # quaternion orientation
        self.qw = qw
        self.qx = qx
        self.qy = qy
        self.qz = qz

        self.state = state

    def get_pos(self):
        return self.x, self.y, self.z

    def get_quat(self):
        return self.qx, self.qy, self.qz, self.qw

    def get_euler(self):
        q = np.array(self.get_quat())
        q2 = q * q

        ## calculate direction cosine matrix elements from $quaternions
        xa = q2[0] - q2[1] - q2[2] + q2[3]
        xb = 2 * (q[0] * q[1] + q[2] * q[3])
        xn = 2 * (q[0] * q[2] - q[1] * q[3])
        yn = 2 * (q[1] * q[2] + q[0] * q[3])
        zn = q2[3] + q2[2] - q2[0] - q2[1]

        ##; calculate RA, Dec, Roll from cosine matrix elements
        ra = np.arctan2(xb, xa)
        dec = np.arctan2(xn, np.sqrt(1 - xn ** 2))
        roll = np.arctan2(yn, zn)
        if (ra < 0):
            ra += 2 * np.pi
        if (roll < 0):
            roll += 2 * np.pi

        return roll, dec, ra


class OrbslamPipeline(OpenCVPipeline):
    def __init__(self, orb_voc_path, config_path, enabled=True, visualize=False):
        super(OrbslamPipeline, self).__init__(enabled)

        self.orb_voc_path = orb_voc_path
        self.config_path = config_path
        self.visualize = visualize

        self.orb = None

        self.capture_sub.required_attributes = ("fps", "width", "height")

        self.message_counter = 0
        self.results_tag = "results"
        self.define_service(self.results_tag, OrbslamMessage)

    async def setup(self):
        self.orb = System(self.orb_voc_path, self.config_path, self.capture.width, self.capture.height,
                          Sensor.MONOCULAR)
        self.orb.set_use_viewer(self.visualize)
        self.orb.initialize()

    async def pipeline(self, message):
        self.orb.process_image_mono(message.image, message.timestamp)

        state = self.orb.get_tracking_state()
        # print(state)
        if state == TrackingState.OK:
            current = self.orb.get_trajectory_points()[-1]
            x, y, z, qw, qx, qy, qz = current[1:]
            timestamp = current[0]

            orb_message = OrbslamMessage(self.message_counter, state, x, y, z, qw, qx, qy, qz, timestamp)
        else:
            orb_message = OrbslamMessage(self.message_counter, state)
            self.message_counter += 1

        await self.broadcast(orb_message, self.results_tag)

    async def teardown(self):
        self.orb.shutdown()
