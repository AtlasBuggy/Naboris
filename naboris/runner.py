from naboris import Naboris, NaborisCLI
from naboris_site import app
from atlasbuggy.robot import Robot
from atlasbuggy.uistream.website import Website

naboris = Naboris()
cmdline = NaborisCLI(naboris.actuators)
website = Website("naboris website", False, app)

robot = Robot(naboris, cmdline, website)
robot.run()
