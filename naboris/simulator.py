from naboris import Naboris
from atlasbuggy.robot import Robot
from atlasbuggy.serialstream.file import SerialFile
from atlasbuggy.uistream.camera_viewer import CameraViewer
from atlasbuggy.camerastream.videoplayer import VideoPlayer


class SerialSimulator(SerialFile):
    def __init__(self, naboris, file_name, directory):
        super(SerialSimulator, self).__init__(naboris, file_name, directory)

        self.current_frame = 0

    def receive_command(self, whoiam, timestamp, packet):
        # print(whoiam, timestamp, packet)
        if whoiam == "naboris actuators":
            if packet == "h":
                print(self.dt(), "stop")
            elif packet[0] == "r":
                print(self.dt(), "spinning:", packet)
            elif packet[0] == "d":
                print(self.dt(), "driving:", packet)
            elif packet[0] == "c":
                print(self.dt(), "turret:", packet)

    def receive_user(self, whoiam, timestamp, packet):
        # print(whoiam, self.dt(), packet)
        if whoiam == "NaborisCam":
            self.current_frame = int(packet)


class CameraSimulator(VideoPlayer):
    def __init__(self, video_name, video_directory, serial_simulator):
        super(CameraSimulator, self).__init__(video_name, video_directory)
        self.serial_simulator = serial_simulator

    def update(self):
        # print(self.current_frame / self.fps)
        while self.serial_simulator.current_frame < self.current_frame:
            if not self.serial_simulator.next():
                self.exit()


def main():
    serial_file_name = "15;37;43"
    serial_directory = "2017_May_28"

    video_name = serial_file_name.replace(";", "_")
    video_directory = "naboris/" + serial_directory

    serial_file = SerialSimulator(Naboris(), serial_file_name, serial_directory)
    capture = CameraSimulator(video_name, video_directory, serial_file)
    viewer = CameraViewer(capture, enabled=True, enable_slider=True)
    capture.link_viewer(viewer)

    Robot.run(capture, viewer)


main()
