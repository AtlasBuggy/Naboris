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

    def start(self):
        self.actuators.set_all_leds(5, 5, 5)

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

    def do_sl(self, line):
        if len(line) > 0:
            line = int(line)
        else:
            line = 75
        naboris.actuators.spin(line)

    def do_sr(self, line):
        if len(line) > 0:
            line = int(line)
        else:
            line = 75
        naboris.actuators.spin(-line)

    def do_d(self, line):
        line = line.split(" ")
        try:
            if len(line) > 0:
                angle = int(line[0])
            else:
                angle = 0

            if len(line) > 1:
                speed = int(line[1])
            else:
                speed = 75
            naboris.actuators.drive(speed, angle)
        except ValueError:
            print("Failed to parse input:", repr(line))

    def do_look(self, line):
        if line == "":
            naboris.actuators.set_turret(90, 90)
            print("looking straight")
        elif line == "down":
            naboris.actuators.set_turret(90, 100)
            print("looking down")
        elif line == "up":
            naboris.actuators.set_turret(90, 30)
            print("looking up")
        elif line == "left":
            naboris.actuators.set_turret(30, 90)
            print("looking left")
        elif line == "right":
            naboris.actuators.set_turret(150, 90)
            print("looking right")
        else:
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
        if len(line) > 0:
            line = int(line)
        else:
            line = 255
        naboris.actuators.set_all_leds(line, 0, 0)

    def do_green(self, line):
        if len(line) > 0:
            line = int(line)
        else:
            line = 255
        naboris.actuators.set_all_leds(0, line, 0)

    def do_blue(self, line):
        if len(line) > 0:
            line = int(line)
        else:
            line = 255
        naboris.actuators.set_all_leds(0, 0, line)

    def do_white(self, line):
        if len(line) > 0:
            line = int(line)
        else:
            line = 255
        naboris.actuators.set_all_leds(line, line, line)

command_line = AutonomousCommandline()


def run_commands():
    command_line.cmdloop()
    print("Command line exiting")

t = Thread(target=run_commands)
# t.daemon = True
t.start()

runner.run()
