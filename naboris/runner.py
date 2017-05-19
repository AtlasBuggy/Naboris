from naboris import Naboris
from naboris_cli import NaborisCLI
from naboris_site import NaborisWebsite
from naboris_cam import NaborisCam
from atlasbuggy.robot import Robot
import os

naboris = Naboris(log=True)
camera = NaborisCam()
cmdline = NaborisCLI(naboris.actuators, naboris.sounds)
website = NaborisWebsite(os.getcwd() + "/templates", naboris.actuators, camera)

robot = Robot(naboris, cmdline, website, camera)
robot.run()
