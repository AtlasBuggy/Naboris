from atlasbuggy import Robot
from atlasbuggy import ThreadedStream
from atlasbuggy.subscriptions import *

from atlasbuggy.cameras.videoplayer import VideoPlayer
from atlasbuggy.cmdline import CommandLine


class VideoReceiver(ThreadedStream):
    def __init__(self):
        super(VideoReceiver, self).__init__(True)

        self.capture_tag = "capture"
        self.require_subscription(self.capture_tag, Feed, VideoPlayer)
        self.capture = None
        self.capture_feed = None

    def receive_subscriptions(self, subscriptions):
        self.capture = subscriptions[self.capture_tag].stream
        self.capture_feed = subscriptions[self.capture_tag].queue

    def run(self):
        while self.running():
            while not self.capture_feed.empty():
                print(self.capture_feed.get().shape)


robot = Robot(log_level=10)

cmdline = CommandLine()
video = VideoPlayer(file_name="videos/naboris/2017_Jun_10/21_25_23.mp4")
receiver = VideoReceiver()

receiver.subscribe(Feed(receiver.capture_tag, video))

robot.run(video, receiver, cmdline)
