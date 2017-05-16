import argparse
import cmd
import math
import time
from threading import Thread
# import app

from naboris import Naboris
from atlasbuggy.interface.live import RobotRunner

parser = argparse.ArgumentParser()
parser.add_argument("-l", "--nolog", help="disable logging", action="store_false")
parser.add_argument("-d", "--debug", help="enable debug prints", action="store_true")
args = parser.parse_args()

class NaborisCommandline(cmd.Cmd):
    def do_l(self, line):
        if len(line) > 0:
            line = int(line)
        else:
            line = 75
        naboris.actuators.spin(line)

    def do_r(self, line):
        if len(line) > 0:
            line = int(line)
        else:
            line = 75
        naboris.actuators.spin(-line)

    def do_d(self, line):
        angle = 0
        speed = 75
        if len(line) > 0:
            line = line.split(" ")

            try:
                if len(line) >= 1:
                    angle = int(line[0])

                if len(line) >= 2:
                    speed = int(line[1])
            except ValueError:
                print("Failed to parse input:", repr(line))
        naboris.actuators.drive(speed, angle)

    def do_look(self, line):
        data = line.split(" ")
        if data[0] == "":
            naboris.actuators.look_straight()
        elif data[0] == "down":
            if len(data) > 1:
                value = int(data[1])
                naboris.actuators.look_up(value)
            else:
                naboris.actuators.look_up(100)
        elif data[0] == "up":
            if len(data) > 1:
                value = int(data[1])
                naboris.actuators.look_up(value)
            else:
                naboris.actuators.look_up()
        elif data[0] == "left":
            if len(data) > 1:
                value = int(data[1])
                naboris.actuators.look_left(value)
            else:
                naboris.actuators.look_left()
        elif data[0] == "right":
            if len(data) > 1:
                value = int(data[1])
                naboris.actuators.look_right(value)
            else:
                naboris.actuators.look_right()
        else:
            line = line.split(" ")
            if len(line) == 2:
                yaw, azimuth = line
                naboris.actuators.set_turret(int(yaw), int(azimuth))

    def do_s(self, line):
        naboris.actuators.stop()

    def do_q(self, line):
        runner.exit()
        return True

    def do_red(self, line):
        if len(line) > 0:
            line = int(line)
        else:
            line = 15
        naboris.actuators.set_all_leds(line, 0, 0)

    def do_green(self, line):
        if len(line) > 0:
            line = int(line)
        else:
            line = 15
        naboris.actuators.set_all_leds(0, line, 0)

    def do_blue(self, line):
        if len(line) > 0:
            line = int(line)
        else:
            line = 15
        naboris.actuators.set_all_leds(0, 0, line)

    def do_white(self, line):
        if len(line) > 0:
            line = int(line)
        else:
            line = 15
        naboris.actuators.set_all_leds(line, line, line)

    def do_battery(self, line):
        naboris.actuators.ask_battery()


naboris = Naboris(True, True)
cmd_line = NaborisCommandline()
runner = RobotRunner(naboris, log_dir=None, log_data=False, debug_prints=False, address_formats=["/dev/ttyUSB[0-9]*"])


def run_commands():
    cmd_line.cmdloop()


Thread(target=run_commands).start()

runner.run()
