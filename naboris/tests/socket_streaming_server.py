import asyncio
import os

from atlasbuggy.camera.video.videoplayer import VideoPlayer
from atlasbuggy.camera.viewer.viewer import CameraViewer
from atlasbuggy.robot import Robot
from atlasbuggy.subscriptions import *
from atlasbuggy.website.socket import SocketServer

os.chdir("..")


class MyServer(SocketServer):
    def __init__(self):
        super(MyServer, self).__init__()
        self.video = None
        self.video_feed = None
        self.video_tag = "video"
        self.require_subscription(self.video_tag, Feed)

    def take(self, subscriptions):
        self.video = self.subscriptions[self.video_tag].stream
        self.video_feed = self.subscriptions[self.video_tag].queue

    async def update(self):
        if len(self.client_writers) > 0:
            while not self.video_feed.empty():
                frame = self.video_feed.get()
                bytes_frame = self.video.numpy_to_bytes(frame)
                length = len(bytes_frame).to_bytes(4, 'big')
                preamble = b'\x54'
                message = preamble + length + bytes_frame
                self.write_all(message, append_newline=False)
                self.logger.debug(length)
        await asyncio.sleep(1 / self.video.fps)


robot = Robot(log_level=10)

capture = VideoPlayer(file_name="21_25_23.mp4", directory="videos/naboris/2017_Jun_10", loop_video=True)
socket = MyServer()
viewer = CameraViewer()

socket.subscribe(Feed(socket.video_tag, capture))
viewer.subscribe(Update(viewer.capture_tag, capture))

robot.run(viewer, capture, socket)
