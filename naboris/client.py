from atlasbuggy.cameras.viewer import CameraViewer
from atlasbuggy.robot import Robot
from atlasbuggy.subscriptions import *
from remote.logitech import Logitech
from remote.socket_client import CLI, NaborisSocketClient


class MyCameraViewer(CameraViewer):
    def __init__(self):
        super(MyCameraViewer, self).__init__()
        self.socket = None
        self.delay = 0.03

    def take(self, subscriptions):
        self.socket = subscriptions["socket"].stream

    def get_frame(self):
        return self.socket.frame


robot = Robot()

socket = NaborisSocketClient()
cli = CLI()
logitech = Logitech(enabled=True)
viewer = MyCameraViewer()

cli.subscribe(Subscription("socket", socket))
logitech.subscribe(Subscription("socket", socket))
viewer.subscribe(Subscription("socket", socket))

robot.run(socket, cli, logitech, viewer)
