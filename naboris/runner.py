from naboris import Naboris
from naboris_cli import NaborisCLI
from naboris_site import NaborisWebsite
from naboris_cam import NaborisCam
from atlasbuggy.robot import Robot
import os

log = True

naboris = Naboris(log=log)
camera = NaborisCam(logger=naboris.logger)
cmdline = NaborisCLI(naboris.actuators, naboris.sounds)
website = NaborisWebsite("templates", "static", naboris.actuators, camera, cmdline)

if log:
    camera.start_recording(directory=("naboris", None))

robot = Robot(naboris, cmdline, website, camera)
robot.run()
