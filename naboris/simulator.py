
from naboris import Naboris
from atlasbuggy.robot import Robot
from atlasbuggy.serialstream.file import SerialFile
from atlasbuggy.uistream.camera_viewer import CameraViewer
from atlasbuggy.camerastream.videoplayer import VideoPlayer

class Simulator(SerialFile):
    def __init__(self, naboris, file_name, directory):
        super(Simulator, self).__init__(naboris, file_name, directory)

    def receive_command(self, whoiam, timestamp, packet):
        pass

    def receive_user(self, whoiam, timestamp, packet):
        print(whoiam, timestamp, packet)

serial_file_name = "02;03;20"
serial_directory = "2017_May_28"

video_name = serial_file_name.replace(";", "_")
video_directory = "naboris/" + serial_directory

serial_file = Simulator(Naboris(), serial_file_name, serial_directory)
capture = VideoPlayer(video_name, video_directory)
viewer = CameraViewer(capture, slider_ticks=capture.slider_ticks)
capture.link_slider(viewer.slider_name)

robot = Robot(serial_file, capture, viewer)
robot.run()
