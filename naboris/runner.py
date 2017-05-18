from naboris import Naboris, NaborisCLI, NaborisWebsite
from atlasbuggy.robot import Robot
import os

naboris = Naboris()
cmdline = NaborisCLI(naboris.actuators)
website = NaborisWebsite("naboris website", os.getcwd() + "/templates", naboris.actuators)

robot = Robot(naboris, cmdline, website)
robot.run()
