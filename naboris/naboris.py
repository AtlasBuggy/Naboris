
import time
from atlasbuggy.robot import Robot
from atlasbuggy.interface import run, simulate

from actuators import Actuators

class Naboris(Robot):
    def __init__(self):
        self.actuators = Actuators()
        self.angle = 0

        super(Naboris, self).__init__(self.actuators)

    # def start(self):
    # def received(self):
    def loop(self):
        self.actuators.drive(self.angle, 255)
        self.angle += 5
        if self.angle >= 360:
            self.angle = 0

    def close(self, reason):
        self.actuators.stop()
        self.actuators.release()

naboris = Naboris()
run(naboris, log_dir=None, log_data=False, debug_prints=True, address_formats=["/dev/ttyUSB[0-9]*"])
# simulate("22", "2017_Mar_02", naboris)
