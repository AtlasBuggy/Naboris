from naboris import Naboris
from naboris_pipeline import NaborisPipeline
from atlasbuggy.robot import Robot
from atlasbuggy.serialstream.file import SerialFile
from atlasbuggy.uistream.camera_viewer import CameraViewer
from atlasbuggy.camerastream.videoplayer import VideoPlayer


class SerialSimulator(SerialFile):
    def __init__(self, naboris, file_name, directory):
        super(SerialSimulator, self).__init__(naboris, file_name, directory)

        self.current_frame = 0

    def receive_command(self, whoiam, timestamp, packet):
        if whoiam == "naboris actuators":
            if packet == "h":
                print("%0.4fs:" % self.dt(), "stop")
            elif packet[0] == "r":
                print("%0.4fs:" % self.dt(), "spinning %s" % "right" if bool(int(packet[1:3])) else "left")
            elif packet[0] == "p":
                print(
                    "%0.4fs:" % self.dt(), "driving at %sº at speed %s" % (
                        (1 if packet[1] == "0" else -1) * int(packet[2:5]), int(packet[5:8]))
                )
            elif packet[0] == "c":
                print("%0.4fs:" % self.dt(), "turret:", packet)

    def receive_user(self, whoiam, timestamp, packet):
        if whoiam == "NaborisCam":
            self.current_frame = int(packet)


class CameraSimulator(VideoPlayer):
    def __init__(self, video_name, video_directory, serial_simulator):
        super(CameraSimulator, self).__init__(video_name, video_directory)
        self.serial_simulator = serial_simulator

    def update(self):
        while self.serial_simulator.current_frame < self.current_frame:
            if not self.serial_simulator.next():
                self.exit()


def main():
    serial_file_name = "20;50;16"
    serial_directory = "2017_May_28"

    video_name = serial_file_name.replace(";", "_")
    video_directory = "naboris/" + serial_directory

    naboris = Naboris()
    serial_file = SerialSimulator(naboris, serial_file_name, serial_directory)
    capture = CameraSimulator(video_name, video_directory, serial_file)
    pipeline = NaborisPipeline(capture, naboris)
    viewer = CameraViewer(capture, enabled=True, enable_slider=True)
    capture.link_viewer(viewer)

    Robot.run(capture, viewer, pipeline)


main()
