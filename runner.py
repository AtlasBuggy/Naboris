import matplotlib

matplotlib.use('Agg')

import argparse

from atlasbuggy import Robot
from atlasbuggy.subscriptions import *
from atlasbuggy.plotters import LivePlotter

from naboris import Naboris
from naboris.picamera import PiCamera
from naboris.cli import NaborisCLI
from naboris.site import NaborisWebsite
from naboris.texture.pipeline import TexturePipeline

# from naboris.inception.pipeline import InceptionPipeline


parser = argparse.ArgumentParser()
parser.add_argument("-l", "--log", help="disable logging", action="store_false")
parser.add_argument("-d", "--debug", help="enable debug prints", action="store_true")
args = parser.parse_args()

log = args.log

robot = Robot(write=log)

video_file_name = robot.log_info["file_name"].replace(";", "_")[:-3] + "mp4"
video_directory = "videos/" + robot.log_info["directory"].split("/")[-1]

camera = PiCamera(file_name=video_file_name, directory=video_directory)
naboris = Naboris()
# pipeline = MasazIDepthPipeline("depth_models/coarse", "depth_models/fine", enabled=args.pipeline)
# pipeline = CalibrationPipeline()
pipeline = TexturePipeline(enabled=False)
# pipeline = InceptionPipeline(enabled=True)
cmdline = NaborisCLI()
website = NaborisWebsite("templates", "static")
plotter = LivePlotter(1, close_when_finished=True, enabled=False)

naboris.subscribe(Feed(naboris.pipeline_tag, pipeline, naboris.results_service_tag))
naboris.subscribe(Subscription(naboris.plotter_tag, plotter))

cmdline.subscribe(Subscription(cmdline.naboris_tag, naboris))
cmdline.subscribe(Subscription(cmdline.capture_tag, camera))
pipeline.subscribe(Update(pipeline.capture_tag, camera))

website.subscribe(Subscription(website.cmd_tag, cmdline))
website.subscribe(Update(website.camera_tag, camera, enabled=False))
website.subscribe(Update(website.pipeline_tag, pipeline, enabled=False))
# website.subscribe(Subscription(website.plotter_tag, plotter))

robot.run(camera, naboris, pipeline, cmdline, website)
