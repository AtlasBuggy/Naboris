import logging
from mylms import MyLMS
from atlasbuggy.robot import Robot

log = False

robot = Robot(write=log, log_level=logging.DEBUG)
lms200 = MyLMS(True, make_image=log)
robot.run(lms200, lms200.plotter)
