from actuators import Actuators
from atlasbuggy.serialstream import SerialStream
from atlasbuggy.iostream.cmdline import CommandLine


class NaborisCLI(CommandLine):
    def __init__(self, actuators):
        super(NaborisCLI, self).__init__("cmdline", False)
        self.actuators = actuators

    def handle_input(self, line):
        if line == 'q':
            self.exit()


class Naboris(SerialStream):
    def __init__(self):
        self.actuators = Actuators()
        self.link_callback(self.actuators, self.receive_actuators)
        super(Naboris, self).__init__("naboris serial", self.actuators)

    def start(self):
        self.actuators.set_turret(90, 70)
        self.actuators.set_turret(90, 90)
        self.actuators.set_all_leds(5, 5, 5)
        self.actuators.set_battery(4800, 5039)

    def receive_actuators(self, timestamp, packet):
        print(packet)

    def request_battery(self):
        self.actuators.ask_battery()

    def close(self):
        self.actuators.stop()
        self.actuators.release()
