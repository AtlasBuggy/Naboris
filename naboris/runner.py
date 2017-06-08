import argparse
from naboris.camera import NaborisCam
from naboris.cli import NaborisCLI
from naboris.pipeline import NaborisPipeline
from naboris.site import NaborisWebsite
from naboris.socket_server import NaborisSocketServer
from naboris import Naboris

from atlasbuggy.cameras.picamera.pivideo import PiVideoRecorder as Recorder
# from atlasbuggy.cameras.cvcamera.cvvideo import CvVideoRecorder as Recorder
from atlasbuggy.files.logger import Logger
from atlasbuggy.robot import Robot

parser = argparse.ArgumentParser()
parser.add_argument("-l", "--log", help="enable logging", action="store_true")
parser.add_argument("-d", "--debug", help="enable debug prints", action="store_true")
parser.add_argument("-pipe", "--pipeline", help="enable pipeline", action="store_true")
args = parser.parse_args()

log = args.log

logger = Logger(enabled=log)
recorder = Recorder(
    logger.input_name.replace(";", "_") + ".mp4",
    ("naboris", logger.input_dir),
    enabled=log,
    debug=True
)
camera = NaborisCam(logger, recorder)
naboris = Naboris(logger, camera)
pipeline = NaborisPipeline(naboris.actuators, args.pipeline, camera)
cmdline = NaborisCLI(naboris)
website = NaborisWebsite("templates", "static", naboris.actuators, camera, pipeline, cmdline)
socket = NaborisSocketServer(cmdline)

Robot.run(socket, pipeline, naboris, cmdline, website, camera)
