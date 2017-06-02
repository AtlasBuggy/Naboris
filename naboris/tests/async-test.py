# This file is meant to collect data from manual control. Terminal interface only
import argparse
# from threading import Thread
import asyncio
import cmd
from http.server import HTTPServer, SimpleHTTPRequestHandler

from atlasbuggy.interface.live import RobotRunner

from atlasbuggy.robot import Robot
from naboris.actuators import Actuators

parser = argparse.ArgumentParser()
parser.add_argument("-l", "--nolog", help="disable logging", action="store_false")
parser.add_argument("-d", "--debug", help="enable debug prints", action="store_true")
args = parser.parse_args()


class Website:
    def __init__(self):
        self.protocol = "HTTP/1.0"
        self.server_address = "127.0.0.1", 8000
        self.server = HTTPServer(self.server_address, SimpleHTTPRequestHandler)

    def run(self):
        socket_info = self.server.socket.getsockname()
        print("Serving HTTP on '%s' port %s..." % (socket_info[0], socket_info[1]))



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


naboris = Naboris()
website = Website()
runner = RobotRunner(naboris, log_dir=None, log_data=False, debug_prints=False, address_formats=["/dev/ttyUSB[0-9]*"])
command_line = AutonomousCommandline()


async def async_robot_run():
    runner.run()


async def async_command_line():
    command_line.cmdloop()


async def async_website_run():
    website.run()


loop = asyncio.get_event_loop()

asyncio.ensure_future(async_robot_run())
asyncio.ensure_future(async_command_line())
asyncio.ensure_future(async_website_run())

loop.run_forever()
