from atlasbuggy.robot import Robot
from atlasbuggy.datastreams.core.serialstream import SerialStream
from actuators import Actuators


class Naboris(Robot):
    def __init__(self):
        self.actuators = Actuators()
        serial = SerialStream(self.actuators)

        super(Naboris, self).__init__(serial)

    def start(self):
        self.actuators.set_all_leds(5, 5, 5)
        self.actuators.set_battery(4800, 5039)

    def request_battery(self):
        self.actuators.ask_battery()

    # def received(self):
    # def loop(self):

    def close(self, reason):
        self.actuators.stop()
        self.actuators.release()
