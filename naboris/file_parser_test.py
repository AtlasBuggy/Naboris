from atlasbuggy.serialstream.file import SerialFile
from naboris import Naboris
from atlasbuggy.robot import Robot

serial_file = SerialFile(Naboris(), "13;49;30", "2017_May_19")

robot = Robot(serial_file)
robot.run()
