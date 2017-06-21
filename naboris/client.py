from atlasbuggy.cameras.cameraviewer import CameraViewer
from remote.socket_client import NaborisSocketClient, CLI
from remote.logitech import Logitech
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


robot = Robot(log_level=10)

socket = NaborisSocketClient()
cli = CLI()
logitech = Logitech()
viewer = MyCameraViewer()

cli.give(socket=socket)
logitech.give(socket=socket)
viewer.give(socket=socket)

robot.run(socket, cli, logitech, viewer)
