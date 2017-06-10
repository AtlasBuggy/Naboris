import logging
from mylms import MyLMS
from atlasbuggy.robot import Robot
from atlasbuggy.cmdline import CommandLine


class LmsCmd(CommandLine):
    def __init__(self):
        super(LmsCmd, self).__init__(log_level=logging.INFO)
        self.lms200 = None

    def take(self):
        self.lms200 = self.streams["lms200"]

    def handle_input(self, line):
        if line == "q":
            self.exit_all()
        elif line[0] == "b":
            packet_bytes = eval(line)
            assert type(packet_bytes) == bytes

            self.lms200.write_telegram(0, packet_bytes)


lms200 = MyLMS(True, True)
cmd = LmsCmd()

robot = Robot(lms200, cmd, lms200.plotter)
robot.init_logger()

cmd.give(lms200=lms200)

robot.run()
