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
        return self.qw, self.qx, self.qy, self.qz


class OrbslamPipeline(OpenCVPipeline):
    def __init__(self, orb_voc_path, config_path, enabled=True, visualize=False):
        super(OrbslamPipeline, self).__init__(enabled)

        self.orb_voc_path = orb_voc_path
        self.config_path = config_path
        self.visualize = visualize

        self.orb = None

        self.capture_sub.required_attributes = ("fps", "width", "height")

        self.message_counter = 0
        self.trajectory_tag = "trajectory"
        self.define_service(self.trajectory_tag, OrbslamMessage)

    async def setup(self):
        self.orb = System(self.orb_voc_path, self.config_path, self.capture.width, self.capture.height,
                          Sensor.MONOCULAR)
        self.orb.set_use_viewer(self.visualize)
        self.orb.initialize()

    async def pipeline(self, message):
        self.orb.process_image_mono(message.image, message.timestamp)

        state = self.orb.get_tracking_state()
        print(state)
        if state == TrackingState.OK:
            current = self.orb.get_trajectory_points()[-1]
            x, y, z, qw, qx, qy, qz = current[1:]
            timestamp = current[0]

            orb_message = OrbslamMessage(self.message_counter, state, x, y, z, qw, qx, qy, qz, timestamp)
        else:
            orb_message = OrbslamMessage(self.message_counter, state)
            self.message_counter += 1

        await self.broadcast(orb_message, self.trajectory_tag)

    async def teardown(self):
        self.orb.shutdown()