from actuators import Actuators
from atlasbuggy.serialstream import SerialStream
from atlasbuggy.filestream.soundfiles import SoundStream


class Naboris(SerialStream):
    def __init__(self, log=False, enabled=True):
        self.actuators = Actuators()
        super(Naboris, self).__init__(self.actuators, log=log, enabled=enabled)

        self.link_callback(self.actuators, self.receive_actuators)
        self.link_recurring(10, self.request_battery)

        self.sounds = SoundStream("sounds", "/home/pi/Music/Bastion/")

    def serial_start(self):
        self.actuators.set_all_leds(15, 15, 15)
        self.actuators.set_battery(5050, 5180)

    def receive_actuators(self, timestamp, packet):
        pass

    def request_battery(self):
        self.actuators.ask_battery()

    def serial_close(self):
        self.actuators.stop()
        self.actuators.release()
