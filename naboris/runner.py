import argparse

# from atlasbuggy.cameras.cvcamera.cvvideo import CvVideoRecorder as Recorder
from atlasbuggy import Robot
from atlasbuggy.cameras.picamera.pivideo import PiVideoRecorder as Recorder
from atlasbuggy.subscriptions import *
from naboris import Naboris
from naboris.camera import NaborisCam
from naboris.cli import NaborisCLI
from naboris.pipeline import NaborisPipeline
from naboris.site import NaborisWebsite
from naboris.socket_server import NaborisSocketServer

parser = argparse.ArgumentParser()
parser.add_argument("-l", "--log", help="enable logging", action="store_true")
parser.add_argument("-d", "--debug", help="enable debug prints", action="store_true")
parser.add_argument("-pipe", "--pipeline", help="enable pipeline", action="store_true")
args = parser.parse_args()

log = args.log

robot = Robot(write=log)

camera = NaborisCam()
naboris = Naboris()
pipeline = NaborisPipeline(args.pipeline)
cmdline = NaborisCLI()
website = NaborisWebsite("templates", "static")
socket = NaborisSocketServer()

video_file_name = robot.log_info["file_name"].replace(";", "_")[:-3] + "mp4"
video_directory = "videos/naboris/" + robot.log_info["directory"].split("/")[-1]
recorder = Recorder(
    video_file_name,
    video_directory,
    enabled=log,
)

camera.subscribe(Subscription(camera.recorder_tag, recorder))
recorder.subscribe(Subscription(recorder.capture_tag, camera))

pipeline.subscribe(Feed(pipeline.capture_tag, camera))

website.subscribe(Subscription(website.actuators_tag, naboris.actuators))
website.subscribe(Subscription(cmdline, cmdline))
website.subscribe(Update(website.camera_tag, camera, enabled=False))
website.subscribe(Update(website.pipeline_tag, pipeline, enabled=False))

socket.subscribe(Update(socket.camera_tag, camera, enabled=False))

robot.run(camera, naboris, pipeline, cmdline, website, socket)
