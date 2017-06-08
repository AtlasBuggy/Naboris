
from atlasbuggy.robot import Robot
from atlasbuggy.sensors.lms200 import LMS200


Robot.run(LMS200("/dev/cu.usbserial"))
