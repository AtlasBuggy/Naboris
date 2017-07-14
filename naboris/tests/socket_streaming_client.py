import cv2
import numpy as np

from atlasbuggy.cameras.viewer.viewer import CameraViewer
from atlasbuggy.robot import Robot
from atlasbuggy.website.socket import SocketClient
from atlasbuggy.subscriptions import *


class MyCameraViewer(CameraViewer):
    def __init__(self):
        super(MyCameraViewer, self).__init__()
        self.socket = None
        self.socket_feed = None
        self.socket_tag = "socket"
        self.delay = 0.05

    def take(self, subscriptions):
        self.socket = subscriptions["socket"].stream
        self.socket_feed = subscriptions["socket"].queue

    def get_frame(self):
        if self.socket_feed.empty():
            return None
        else:
            return self.socket_feed.get()


class MySocket(SocketClient):
    def __init__(self, enabled=True):
        super(MySocket, self).__init__("something interesting", "0.0.0.0", enabled=enabled, timeout=10)
        self.frame = None

    async def update(self):
        if await self.read(1) == b'\x54':
            length = int.from_bytes(await self.read(4), 'big')
            bytes_frame = await self.read(length)
            self.post(self.to_image(bytes_frame))

    def to_image(self, byte_stream):
        return cv2.imdecode(np.fromstring(byte_stream, dtype=np.uint8), 1)


robot = Robot(log_level=10)

viewer = MyCameraViewer()
socket = MySocket()

viewer.subscribe(Update(viewer.socket_tag, socket))

robot.run(viewer, socket)
