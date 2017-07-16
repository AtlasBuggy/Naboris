import argparse

from atlasbuggy import Robot
from atlasbuggy.subscriptions import *
from naboris import Naboris
from naboris.picamera import PiCamera
from naboris.cli import NaborisCLI
from naboris.pipeline import NaborisPipeline, CalibrationPipeline
from naboris.site import NaborisWebsite
from naboris.socket_server import NaborisSocketServer

parser = argparse.ArgumentParser()
parser.add_argument("-l", "--log", help="disable logging", action="store_false")
parser.add_argument("-d", "--debug", help="enable debug prints", action="store_true")
parser.add_argument("-pipe", "--pipeline", help="enable pipeline", action="store_true")
args = parser.parse_args()

log = args.log

robot = Robot(write=log)

video_file_name = robot.log_info["file_name"].replace(";", "_")[:-3] + "mp4"
video_directory = "videos/" + robot.log_info["directory"].split("/")[-1]

camera = PiCamera(file_name=video_file_name, directory=video_directory)
naboris = Naboris()
pipeline = NaborisPipeline(args.pipeline)
# pipeline = CalibrationPipeline()
cmdline = NaborisCLI()
website = NaborisWebsite("templates", "static")
socket = NaborisSocketServer(enabled=False)

naboris.subscribe(Feed(naboris.pipeline_tag, pipeline, naboris.results_service_tag))

cmdline.subscribe(Subscription(cmdline.naboris_tag, naboris))
cmdline.subscribe(Subscription(cmdline.capture_tag, camera))
pipeline.subscribe(Update(pipeline.capture_tag, camera))

website.subscribe(Subscription(website.cmd_tag, cmdline))
website.subscribe(Update(website.camera_tag, camera, enabled=False))
website.subscribe(Update(website.pipeline_tag, pipeline, enabled=False))

socket.subscribe(Update(socket.camera_tag, camera, enabled=False))
socket.subscribe(Subscription(socket.cmdline_tag, cmdline))

robot.run(camera, naboris, pipeline, cmdline, website, socket)
