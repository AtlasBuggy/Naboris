import cv2
import numpy as np
from atlasbuggy.cameras.cameraviewer import CameraViewer
from atlasbuggy.website.socket import SocketClient
from atlasbuggy.robot import Robot


class MyCameraViewer(CameraViewer):
    def __init__(self):
        super(MyCameraViewer, self).__init__()
        self.socket = None
        self.delay = 0.05

    def take(self):
        self.socket = self.streams["socket"]

    def get_frame(self):
        return self.socket.frame


class MySocket(SocketClient):
    def __init__(self, enabled=True):
        super(MySocket, self).__init__("something interesting", "0.0.0.0", enabled=enabled, timeout=10)
        self.length = 0
        self.bytes_frame = b''
        self.frame = None

    async def update(self):
        if await self.read(1) == b'\x54':
            self.length = int.from_bytes(await self.read(4), 'big')
            self.bytes_frame = await self.read(self.length)
            self.frame = self.to_image(self.bytes_frame)

    def to_image(self, byte_stream):
        return cv2.imdecode(np.fromstring(byte_stream, dtype=np.uint8), 1)


robot = Robot(log_level=10)

viewer = MyCameraViewer()
socket = MySocket()

viewer.give(socket=socket)

robot.run(viewer, socket)
