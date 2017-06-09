import argparse
from naboris.camera import NaborisCam
from naboris.cli import NaborisCLI
from naboris.pipeline import NaborisPipeline
from naboris.site import NaborisWebsite
from naboris.socket_server import NaborisSocketServer
from naboris import Naboris

from atlasbuggy.cameras.picamera.pivideo import PiVideoRecorder as Recorder
# from atlasbuggy.cameras.cvcamera.cvvideo import CvVideoRecorder as Recorder
from atlasbuggy.robot import Robot

parser = argparse.ArgumentParser()
parser.add_argument("-l", "--log", help="enable logging", action="store_true")
parser.add_argument("-d", "--debug", help="enable debug prints", action="store_true")
parser.add_argument("-pipe", "--pipeline", help="enable pipeline", action="store_true")
args = parser.parse_args()

log = args.log

camera = NaborisCam()
naboris = Naboris()
pipeline = NaborisPipeline(args.pipeline)
cmdline = NaborisCLI()
website = NaborisWebsite("templates", "static")
socket = NaborisSocketServer()

robot = Robot(socket, pipeline, naboris, cmdline, website, camera)
robot.init_logger(write=log)

video_file_name = robot.log_info["file_name"].replace(";", "_") + ".mp4"
video_directory = "naboris/" + robot.log_info["directory"].split("/")[-1]
recorder = Recorder(
    video_file_name,
    video_directory,
    enabled=log,
    debug=True
)

camera.give(recorder=recorder)
pipeline.give(actuators=naboris.actuators, camera=camera)
cmdline.give(naboris=naboris)
website.give(naboris=naboris, camera=camera, pipeline=pipeline, cmdline=cmdline)
socket.give(cmdline=cmdline)

robot.run()
