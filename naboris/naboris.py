# This file is meant to collect data from manual control. Terminal interface only
import argparse
import cmd
import math
import time
from threading import Thread
import datetime

from atlasbuggy.robot import Robot
from atlasbuggy.interface.live import RobotRunner

from actuators import Actuators

class Naboris(Robot):
    def __init__(self):
        self.actuators = Actuators()

        super(Naboris, self).__init__(self.actuators)

    # def start(self):
    # def received(self):
    # def loop(self):

    def close(self, reason):
        self.actuators.stop()
        self.actuators.release()

parser = argparse.ArgumentParser()
parser.add_argument("-l", "--nolog", help="disable logging", action="store_false")
parser.add_argument("-d", "--debug", help="enable debug prints", action="store_true")
args = parser.parse_args()


naboris = Naboris()
runner = RobotRunner(naboris, log_dir=None, log_data=False, debug_prints=False, address_formats=["/dev/ttyUSB[0-9]*"])

class AutonomousCommandline(cmd.Cmd):
    def do_circle(self, line):
        naboris.actuators.do_circle()

    def spin(self, speed, line):
        if len(line) > 0:
            for_ms = int(line)
        else:
            for_ms = None
        naboris.actuators.spin(speed, for_ms)

    def do_sl(self, line):
        self.spin(255, line)

    def do_sr(self, line):
        self.spin(-255, line)

    def do_d(self, line):
        line = line.split(" ")
        try:
            speed = int(line[0])
            if len(line) > 1:
                for_ms = int(line[1])
            else:
                for_ms = None
            naboris.actuators.drive(255, speed, for_ms)
        except ValueError:
            print("Failed to parse input:", repr(line))

    def do_look(self, line):
        line = line.split(" ")
        if len(line) == 2:
            yaw, azimuth = line
            naboris.actuators.set_turret(int(yaw), int(azimuth))

    def do_s(self, line):
        naboris.actuators.stop()

    def do_r(self, line):
        naboris.actuators.release()

    def do_q(self, line):
        runner.exit()
        return True

    def do_red(self, line):
        naboris.actuators.set_all_leds(255, 0, 0)

    def do_green(self, line):
        naboris.actuators.set_all_leds(0, 255, 0)

    def do_blue(self, line):
        naboris.actuators.set_all_leds(0, 0, 255)

    def do_white(self, line):
        naboris.actuators.set_all_leds(255, 255, 255)

command_line = AutonomousCommandline()


def run_commands():
    command_line.cmdloop()
    print("Command line exiting")

t = Thread(target=run_commands)
# t.daemon = True
t.start()

runner.run()
