from atlasbuggy import Robot
from atlasbuggy import ThreadedStream
from atlasbuggy.subscriptions import *

from naboris.camera import NaborisCam
from atlasbuggy.cmdline import CommandLine


class VideoReceiver(ThreadedStream):
    def __init__(self):
        super(VideoReceiver, self).__init__(True)

        self.capture_tag = "capture"
        self.require_subscription(self.capture_tag, Update, NaborisCam)
        self.capture_sub = None
        self.frame_num = 0

    def take(self, subscriptions):
        self.capture_sub = subscriptions[self.capture_tag]

    def run(self):
        while self.running():
            while not self.capture_sub.empty():
                print(self.capture_sub.get().shape, self.frame_num)
                self.frame_num += 1


robot = Robot(log_level=10)

cmdline = CommandLine(enabled=False)
capture = NaborisCam()
receiver = VideoReceiver()

receiver.subscribe(Update(receiver.capture_tag, capture))

robot.run(capture, receiver, cmdline)
