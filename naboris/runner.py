from naboris import Naboris
from naboris_cli import NaborisCLI
from naboris_site import NaborisWebsite
from naboris_cam import NaborisCam
from naboris_pipeline import NaborisPipeline
from atlasbuggy.robot import Robot
from atlasbuggy.filestream.logger import Logger
from atlasbuggy.camerastream.picamera.pivideo import PiVideoRecorder

log = False

logger = Logger(enabled=log)
recorder = PiVideoRecorder(
    logger.input_name.replace(";", "_") + ".mp4",
    ("naboris", logger.input_dir),
    enabled=log
)
camera = NaborisCam(logger, recorder)
pipeline = NaborisPipeline(camera)
naboris = Naboris(pipeline, logger)
cmdline = NaborisCLI(naboris.actuators, naboris.sounds)
website = NaborisWebsite("templates", "static", naboris, camera, pipeline, cmdline)

Robot.run(naboris, cmdline, website, camera, pipeline)
