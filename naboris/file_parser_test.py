from atlasbuggy.filestream.serialfile import SerialFile
from naboris import Naboris
from atlasbuggy.robot import Robot

serial_file = SerialFile("13;49;30", "2017_May_19", Naboris())

robot = Robot(serial_file)
robot.run()
