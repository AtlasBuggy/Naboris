from atlasbuggy.cameras.viewer import CameraViewer
from atlasbuggy.robot import Robot
from atlasbuggy.subscriptions import *
from remote.logitech import Logitech
from remote.socket_client import CLI, NaborisSocketClient


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


robot = Robot()

socket = NaborisSocketClient()
cli = CLI()
logitech = Logitech(enabled=True)
viewer = MyCameraViewer()

cli.subscribe(Subscription("socket", socket))
logitech.subscribe(Subscription("socket", socket))
viewer.subscribe(Update(viewer.socket_tag, socket))

robot.run(socket, cli, logitech, viewer)
