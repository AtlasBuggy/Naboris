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

log = False

logger = Logger(enabled=log)
recorder = Recorder(
    logger.input_name.replace(";", "_") + ".mp4",
    ("naboris", logger.input_dir),
    enabled=log,
    debug=True
)
camera = NaborisCam(logger, recorder)
naboris = Naboris(logger, camera)
pipeline = NaborisPipeline(camera, naboris.actuators)
cmdline = NaborisCLI(naboris.actuators, naboris.sounds)
website = NaborisWebsite("templates", "static", naboris.actuators, camera, pipeline, cmdline)
socket = NaborisSocketServer(cmdline)

Robot.run(socket, pipeline, naboris, cmdline, website, camera)
