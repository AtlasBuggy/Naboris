from atlasbuggy.cameras.videoplayer import VideoPlayer
from atlasbuggy.ui.camera_viewer import CameraViewer

from atlasbuggy.robot import Robot
from naboris import Naboris
from naboris.serial_simulator import NaborisSimulator
from naboris.pipeline import NaborisPipeline


class CameraSimulator(VideoPlayer):
    def __init__(self, video_name, video_directory, serial_simulator, pipeline):
        super(CameraSimulator, self).__init__(video_name, video_directory)
        self.serial_simulator = serial_simulator
        self.pipeline = pipeline
        self.pipeline.capture = self

    def update(self):
        while self.serial_simulator.current_frame < self.current_frame:
            if not self.serial_simulator.next():
                self.exit()
            self.pipeline.update_pipeline(self.frame)

data_sets = {
    "my room": (
        ("20;50", "2017_May_28"),
    ),
    "hallway": (
        ("16;23", "2017_May_28"),
    )
}


serial_file_name, serial_directory = data_sets["hallway"][0]

video_name = serial_file_name.replace(";", "_")
video_directory = "naboris/" + serial_directory

naboris = Naboris()
serial_file = NaborisSimulator(naboris, serial_file_name, serial_directory)
pipeline = NaborisPipeline(naboris, enabled=True, generate_database=True)
capture = CameraSimulator(video_name, video_directory, serial_file, pipeline)
viewer = CameraViewer(capture, pipeline, enabled=True, enable_slider=True)
capture.link_viewer(viewer)

Robot.run(capture, viewer)
