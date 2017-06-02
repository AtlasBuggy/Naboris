import random

from atlasbuggy.files.soundfiles import SoundStream
from atlasbuggy.serial import SerialStream
from atlasbuggy.serial.file import SerialFile

from naboris.actuators import Actuators


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


class SerialSimulator(SerialFile):
    def __init__(self, naboris, file_name, directory):
        super(SerialSimulator, self).__init__(naboris, file_name, directory)

        self.current_frame = 0

    def receive_command(self, whoiam, timestamp, packet):
        if whoiam == "naboris actuators":
            if packet == "h":
                print("%0.4fs:" % self.dt(), "stop")
            elif packet[0] == "r":
                print("%0.4fs:" % self.dt(), "spinning %s" % "right" if bool(int(packet[1:3])) else "left")
            elif packet[0] == "p":
                print(
                    "%0.4fs:" % self.dt(), "driving at %sº at speed %s" % (
                        (1 if packet[1] == "0" else -1) * int(packet[2:5]), int(packet[5:8]))
                )
            elif packet[0] == "c":
                yaw = int(packet[1:4])
                azimuth = int(packet[4:7])
                print("%0.4fs:" % self.dt(), end="looking ")
                if yaw == 90 and azimuth == 90:
                    print("straight")
                else:
                    if yaw > 90:
                        print("left and ", end="")
                    elif yaw < 90:
                        print("right and ", end="")

                    if azimuth == 90:
                        print("straight")
                    elif azimuth > 90:
                        print("up", end="")
                    else:
                        print("down", end="")

                    if yaw == 90:
                        print(" and straight", end="")
                    print()

                    # elif packet[0] == "o":
                    #     print("led: %d %d %d" % (int(packet[4:7]), int(packet[7:10]), int(packet[10:13])))

    def receive_user(self, whoiam, timestamp, packet):
        if whoiam == "NaborisCam":
            self.current_frame = int(packet)
            # elif whoiam == "frame check":
            #     num_frames, frame = packet.split("\t")
            #     print("check:", num_frames)
