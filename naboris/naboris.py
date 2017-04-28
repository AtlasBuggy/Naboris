
from atlasbuggy.robot import Robot
from atlasbuggy.interface import run, simulate

from actuators import Actuators

class Naboris(Robot):
    def __init__(self):
        self.actuators = Actuators()

        super(Naboris, self).__init__(self.actuators)

    # def start(self):
    # def received(self):
    # def loop(self):
    # def close(self):

naboris = Naboris()
run(naboris, log_dir=None, log_data=False, debug_prints=True)
# simulate("22", "2017_Mar_02", naboris)
