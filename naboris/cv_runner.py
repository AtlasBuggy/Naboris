import time
import asyncio

from atlasbuggy.cameras.videoplayer import VideoPlayer
from atlasbuggy.cameras.viewer.trackbar import CameraViewerWithTrackbar
from atlasbuggy.logparser import LogParser
from atlasbuggy.plotters.liveplotter import LivePlotter
from atlasbuggy.robot import Robot
from naboris import Naboris
from naboris.pipeline import NaborisPipeline


class MyCameraViewer(CameraViewerWithTrackbar):
    def __init__(self):
        super(MyCameraViewer, self).__init__(enabled=True)
        self.pipeline = None
        self.pipeline_feed = None
        self.capture_feed = None

        self.show_original = False

    def take(self):
        self.take_capture()
        self.pipeline = self.streams["pipeline"]

    def start(self):
        self.pipeline_feed = self.get_feed(self.pipeline)
        self.capture_feed = self.get_feed(self.capture)

    def check_feed_for_frames(self):
        frame = None
        output = None
        if self.show_original:
            feed = self.capture_feed
        else:
            feed = self.pipeline_feed

        while not feed.empty():
            output = feed.get()

        if output is not None:
            if self.show_original:
                post_bytes = self.capture.post_bytes
            else:
                post_bytes = self.pipeline.post_bytes
            if post_bytes:
                frame, bytes_frame = output
            else:
                frame = output[0]
        return frame

    def key_callback(self, key):
        if key == 'o':
            self.show_original = not self.show_original
            if self.show_original:
                self.disable_feed(self.pipeline)
                self.enable_feed(self.capture)
            else:
                self.disable_feed(self.capture)
                self.enable_feed(self.pipeline)
        elif key == 'q':
            self.exit()
        elif key == ' ':
            self.paused = not self.paused
            self.capture.paused = self.paused
            self.pipeline.paused = self.paused


robot = Robot(log_level=10)

capture = VideoPlayer(file_name="videos/naboris/2017_May_28/16_23_21.mp4")
viewer = MyCameraViewer()
pipeline = NaborisPipeline()

viewer.give(capture=capture, pipeline=pipeline)
pipeline.give(capture=capture)

viewer.subscribe(capture=capture, pipeline=pipeline)
pipeline.subscribe(capture=capture)

robot.run(viewer, capture, pipeline)
