import time
import random
from actuators import Actuators
from atlasbuggy.serialstream import SerialStream
from atlasbuggy.filestream.soundfiles import SoundStream


class Naboris(SerialStream):
    def __init__(self, logger=None, camera=None, debug=False, enabled=True):
        self.actuators = Actuators()
        super(Naboris, self).__init__(self.actuators, logger=logger, debug=debug, enabled=enabled)

        self.link_callback(self.actuators, self.receive_actuators)
        self.link_recurring(10, self.request_battery)
        self.link_recurring(1, self.play_random_sound, include_event_in_params=True)
        self.link_recurring(0.1, self.led_clock)
        self.led_index = 0
        self.prev_led_state = None
        self.link_recurring(0.01, self.check_frame_num)

        self.sounds = SoundStream("sounds", "/home/pi/Music/Bastion/")
        self.random_sound_folders = ["humming", "curiousity", "nothing", "confusion", "concern", "sleepy", "vibrating"]
        self.camera = camera

    def serial_start(self):
        self.actuators.set_all_leds(5, 5, 5)
        self.actuators.set_battery(5050, 5180)

    def play_random_sound(self, event):
        event.repeat_time = random.randint(30, 120)  # play a random sound every 30..120 seconds
        folder = random.choice(self.random_sound_folders)
        sound = random.choice(self.sounds.list_sounds(folder))
        self.sounds.play(sound)

    def receive_actuators(self, timestamp, packet):
        pass

    def check_frame_num(self):
        self.record(time.time(), "frame check", "%s\t%s" % (self.camera.num_frames, self.camera.frame[0][0]))

    def led_clock(self):
        self.prev_led_state = self.actuators.get_led(self.led_index)

        self.actuators.set_led(self.led_index, 0, 128, 255, show=False)
        self.actuators.set_led((self.led_index - 1) % self.actuators.num_leds, self.prev_led_state)

        self.led_index += 1
        if self.led_index >= self.actuators.num_leds:
            self.led_index = 0

    def request_battery(self):
        self.actuators.ask_battery()

    def serial_close(self):
        self.actuators.stop()
        self.actuators.release()
