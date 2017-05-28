import random
from actuators import Actuators
from atlasbuggy.serialstream import SerialStream
from atlasbuggy.filestream.soundfiles import SoundStream


class Naboris(SerialStream):
    def __init__(self, log=False, enabled=True):
        self.actuators = Actuators()
        super(Naboris, self).__init__(self.actuators, log=log, enabled=enabled)

        self.link_callback(self.actuators, self.receive_actuators)
        self.link_recurring(10, self.request_battery)
        # self.link_recurring(1, self.play_random_sound, include_event_in_params=True)

        self.sounds = SoundStream("sounds", "/home/pi/Music/Bastion/")
        self.random_sound_folders = ["humming", "curiousity", "nothing", "confusion", "concern", "sleepy", "vibrating"]

    def serial_start(self):
        self.actuators.set_all_leds(15, 15, 15)
        self.actuators.set_battery(5050, 5180)

    def play_random_sound(self, event):
        event.repeat_time = random.randint(30, 120)  # play a random sound every 30..120 seconds
        folder = random.choice(self.random_sound_folders)
        sound = random.choice(self.sounds.list_sounds(folder))
        self.sounds.play(sound)

    def receive_actuators(self, timestamp, packet):
        pass

    def request_battery(self):
        self.actuators.ask_battery()

    def serial_close(self):
        self.actuators.stop()
        self.actuators.release()
