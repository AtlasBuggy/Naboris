import logging
from mylms import MyLMS
from atlasbuggy.robot import Robot

robot = Robot(write=True, log_level=logging.DEBUG)

lms200 = MyLMS(True)

robot.run(lms200, lms200.plotter)
