import re
import os
from atlasbuggy.extras.cmdline import CommandLine


class NaborisCLI(CommandLine):
    def __init__(self, enabled=True, log_level=None):
        super(NaborisCLI, self).__init__(enabled, log_level)
        self.naboris = None
        self.actuators = None
        self.sounds = None
        self.capture = None

        self.naboris_tag = "naboris"
        self.capture_tag = "capture"

        self.video_num_counter_regex = r"([\s\S]*)-([0-9]*)\.([\S]*)"
        self.video_name_regex = r"([\s\S]*)\.([\S]*)"

        self.require_subscription(self.naboris_tag)
        self.require_subscription(self.capture_tag)

    def take(self, subscriptions):
        self.naboris = subscriptions[self.naboris_tag].get_stream()
        self.capture = subscriptions[self.capture_tag].get_stream()
        self.actuators = self.naboris.actuators
        self.sounds = self.naboris.sounds

    def spin_left(self, params):
        value = int(params) if len(params) > 0 else 75
        self.actuators.spin(value)

    def spin_right(self, params):
        value = int(params) if len(params) > 0 else 75
        self.actuators.spin(-value)

    def drive(self, params):
        angle = 0
        speed = 75
        angular = 0
        if len(params) > 1:
            values = params.split(" ")

            try:
                if len(values) >= 1:
                    angle = int(values[0])

                if len(values) >= 2:
                    speed = int(values[1])

                if len(values) >= 3:
                    angular = int(values[2])
            except ValueError:
                print("Failed to parse input:", repr(values))
        self.actuators.drive(speed, angle, angular)

    def look(self, params):
        data = params.split(" ")
        if data[0] == "":
            self.actuators.look_straight()
        elif data[0] == "down":
            if len(data) > 1:
                value = int(data[1])
                self.actuators.look_up(value)
            else:
                self.actuators.look_down()
        elif data[0] == "up":
            if len(data) > 1:
                value = int(data[1])
                self.actuators.look_up(value)
            else:
                self.actuators.look_up()
        elif data[0] == "left":
            if len(data) > 1:
                value = int(data[1])
                self.actuators.look_left(value)
            else:
                self.actuators.look_left()
        elif data[0] == "right":
            if len(data) > 1:
                value = int(data[1])
                self.actuators.look_right(value)
            else:
                self.actuators.look_right()
        else:
            if len(data) == 2:
                yaw, azimuth = data
                self.actuators.set_turret(int(yaw), int(azimuth))

    def rgb(self, params):
        r, g, b = [int(x) for x in params.split(" ")]
        self.actuators.set_all_leds(r, g, b)

    def red(self, params):
        value = int(params) if len(params) > 0 else 15
        self.actuators.set_all_leds(value, 0, 0)

    def green(self, params):
        value = int(params) if len(params) > 0 else 15
        self.actuators.set_all_leds(0, value, 0)

    def blue(self, params):
        value = int(params) if len(params) > 0 else 15
        self.actuators.set_all_leds(0, 0, value)

    def white(self, params):
        value = int(params) if len(params) > 0 else 15
        self.actuators.set_all_leds(value, value, value)

    def battery(self, params):
        self.actuators.ask_battery()

    def set_autonomous(self, params=None):
        self.logger.debug("Enabling autonomous mode")
        self.naboris.autonomous = True
        self.actuators.stop()

    def set_manual(self, params=None):
        self.logger.debug("Enabling manual mode")
        self.naboris.autonomous = False
        self.actuators.stop()

    def my_exit(self, params):
        self.exit()

    def my_stop(self, params):
        self.actuators.stop()

    def say_hello(self, params):
        self.sounds.play("emotes/hello")
        self.actuators.pause(0.5)
        self.actuators.set_all_leds(0, 0, 15)
        self.actuators.look_straight()
        self.actuators.pause(0.25)
        for _ in range(2):
            self.actuators.look_up()
            self.actuators.pause(0.25)
            self.actuators.look_down()
            self.actuators.pause(0.25)
        self.actuators.look_straight()
        self.actuators.set_all_leds(15, 15, 15)

    def say_alert(self, params):
        self.sounds.play("alert/high_alert")
        self.actuators.pause(0.5)
        self.actuators.set_all_leds(15, 0, 0)
        self.actuators.pause(0.05)
        self.actuators.look_straight()
        for _ in range(3):
            self.actuators.look_left()
            self.actuators.pause(0.15)
            self.actuators.look_right()
            self.actuators.pause(0.15)
        self.actuators.look_straight()
        self.actuators.pause(0.1)
        self.actuators.set_all_leds(15, 15, 15)

    def say_random_sound(self, params):
        self.naboris.play_random_sound()

    def start_new_video(self, params):
        if not self.capture.is_recording:
            matches = re.findall(self.video_num_counter_regex, self.capture.file_name)
            if len(matches) == 0:
                name_matches = re.findall(self.video_name_regex, self.capture.file_name)
                file_name_no_ext, extension = name_matches[0]
                new_file_name = "%s-1.%s" % (file_name_no_ext, extension)
            else:
                file_name_no_ext, counter, extension = matches[0]
                counter = int(counter) + 1
                new_file_name = "%s-%s.%s" % (file_name_no_ext, counter, extension)

            self.capture.start_recording(new_file_name, self.capture.directory)
        else:
            print("PiCamera already recording")

    def stop_recording(self, params):
        if self.capture.is_recording:
            self.capture.stop_recording()
        else:
            print("PiCamera already stopped recording")

    def check_commands(self, line, **commands):
        function = None
        current_command = ""
        for command, fn in commands.items():
            if line.startswith(command) and len(command) > len(current_command):
                function = fn
                current_command = command
        if function is not None:
            function(line[len(current_command):].strip(" "))

    def handle_input(self, line):
        if type(line) == str:
            self.check_commands(
                line,
                q=self.my_exit,
                l=self.spin_left,
                r=self.spin_right,
                d=self.drive,
                look=self.look,
                s=self.my_stop,
                red=self.red,
                green=self.green,
                blue=self.blue,
                white=self.white,
                rgb=self.rgb,
                battery=self.battery,
                hello=self.say_hello,
                alert=self.say_alert,
                sound=self.say_random_sound,
                start_video=self.start_new_video,
                stop_video=self.stop_recording,
                manual=self.set_manual,
                auton=self.set_autonomous
            )
