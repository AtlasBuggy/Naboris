from naboris import Naboris, NaborisCLI
from atlasbuggy.robot import Robot
from atlasbuggy.uistream.website import Website
import os

naboris = Naboris()
cmdline = NaborisCLI(naboris.actuators)
website = Website("naboris website", os.getcwd() + "/templates")

robot = Robot(naboris, cmdline, website)
robot.run()
