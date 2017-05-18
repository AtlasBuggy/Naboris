from actuators import Actuators
from atlasbuggy.datastreams.serialstream import SerialStream
from atlasbuggy.robot import Robot


class Naboris(Robot):
    def __init__(self):
        self.actuators = Actuators()
        serial = SerialStream(self.actuators)

        super(Naboris, self).__init__(serial)

    def start(self):
        self.actuators.set_turret(90, 70)
        self.actuators.set_turret(90, 90)
        self.actuators.set_all_leds(5, 5, 5)
        self.actuators.set_battery(4800, 5039)

    def request_battery(self):
        self.actuators.ask_battery()

    # def received(self):
    # def loop(self):

    def close(self, reason):
        self.actuators.stop()
        self.actuators.release()
