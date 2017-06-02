from atlasbuggy.camerastream.videoplayer import VideoPlayer
from atlasbuggy.uistream.camera_viewer import CameraViewer

from atlasbuggy.robot import Robot
from naboris import Naboris, SerialSimulator
from naboris.pipeline import NaborisPipeline


class CameraSimulator(VideoPlayer):
    def __init__(self, video_name, video_directory, serial_simulator):
        super(CameraSimulator, self).__init__(video_name, video_directory)
        self.serial_simulator = serial_simulator

    def update(self):
        while self.serial_simulator.current_frame < self.current_frame:
            if not self.serial_simulator.next():
                self.exit()


serial_file_name = "22;06;03"
serial_directory = "2017_May_29"

video_name = serial_file_name.replace(";", "_")
video_directory = "naboris/" + serial_directory

naboris = Naboris()
serial_file = SerialSimulator(naboris, serial_file_name, serial_directory)
capture = CameraSimulator(video_name, video_directory, serial_file)
pipeline = NaborisPipeline(capture, naboris, enabled=True)
viewer = CameraViewer(capture, pipeline, enabled=True, enable_slider=True)
capture.link_viewer(viewer)

Robot.run(capture, viewer, pipeline)
