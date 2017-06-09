
from mylms import MyLMS, plotter
from atlasbuggy.robot import Robot
from atlasbuggy.ui.cmdline import CommandLine
from atlasbuggy.files.logger import Logger


class LmsCmd(CommandLine):
    def __init__(self):
        super(LmsCmd, self).__init__(False)

    def handle_input(self, line):
        print(line)


logger = Logger()
lms200 = MyLMS(True, logger)
# cmd = LmsCmd()

Robot.run(lms200, plotter)
