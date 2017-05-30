from naboris import Naboris
from naboris_cli import NaborisCLI
from naboris_site import NaborisWebsite
from naboris_cam import NaborisCam
from naboris_pipeline import NaborisPipeline
from atlasbuggy.robot import Robot
from atlasbuggy.filestream.logger import Logger
from atlasbuggy.camerastream.picamera.pivideo import PiVideoRecorder

log = True

logger = Logger(enabled=log)
recorder = PiVideoRecorder(
    logger.input_name.replace(";", "_") + ".mp4",
    ("naboris", logger.input_dir),
    enabled=log
)
camera = NaborisCam(logger, recorder)
naboris = Naboris(logger, camera)
pipeline = NaborisPipeline(camera, naboris.actuators)
cmdline = NaborisCLI(naboris.actuators, naboris.sounds)
website = NaborisWebsite("templates", "static", naboris.actuators, camera, pipeline, cmdline)

Robot.run(pipeline, naboris, cmdline, website, camera)
