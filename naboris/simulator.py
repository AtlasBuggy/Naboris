from atlasbuggy.cameras.camera_viewer import CameraViewer
from atlasbuggy.cameras.videoplayer import VideoPlayer
from atlasbuggy.logparser import LogParser
from atlasbuggy.robot import Robot
from naboris import Naboris
from naboris.pipeline import NaborisPipeline


class Simulator(LogParser):
    def __init__(self, file_name, directory, enabled=True, log_level=None):
        super(Simulator, self).__init__(file_name, directory, enabled, log_level=log_level)
        self.naboris = None

    def take(self):
        self.naboris = self.streams["naboris"]

    def update(self):
        pass


