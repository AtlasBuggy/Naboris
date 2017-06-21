import asyncio
import os

from atlasbuggy.cameras.videoplayer import VideoPlayer
from atlasbuggy.cameras.viewer.trackbar import CameraViewerWithTrackbar
from atlasbuggy.robot import Robot
from atlasbuggy.website.socket import SocketServer

os.chdir("..")


class MyServer(SocketServer):
    def __init__(self):
        super(MyServer, self).__init__()
        self.video = None

    def take(self):
        self.video = self.streams["video"]

    async def update(self):
        if len(self.client_writers) > 0:
            if self.video.frame is not None:
                bytes_frame = self.video.get_bytes_frame()
                length = len(bytes_frame).to_bytes(4, 'big')
                preamble = b'\x54'
                message = preamble + length + bytes_frame
                self.write_all(message, append_newline=False)
                self.logger.debug(length)
        await asyncio.sleep(1 / self.video.fps)


robot = Robot(log_level=10)

capture = VideoPlayer("21_25_23.mp4", "videos/naboris/2017_Jun_10", loop_video=True)
socket = MyServer()
viewer = CameraViewerWithTrackbar()

socket.give(video=capture)
viewer.give(video_player=capture)

robot.run(viewer, capture, socket)
