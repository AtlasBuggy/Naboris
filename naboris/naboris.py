import time
from actuators import Actuators
from atlasbuggy.serialstream import SerialStream
from atlasbuggy.iostream.cmdline import CommandLine
from flask import Flask, render_template, Response, request
from camera_pi import Camera
from atlasbuggy.uistream.website import Website
from atlasbuggy.filestream.soundfiles import SoundStream

class NaborisWebsite(Website):
    def __init__(self, name, template_folder, actuators, enabled=True):
        super(NaborisWebsite, self).__init__(name, template_folder, enabled)

        self.app.add_url_rule("/video_feed", view_func=self.video_feed)
        self.app.add_url_rule("/lights", view_func=self.lights, methods=['POST'])
        # self.app.add_url_rule("/lights_off", view_func=self.lights_off)
        self.actuators = actuators

    def index(self):
        return render_template('index.html')

    def gen(self, camera):
        """Video streaming generator function."""
        while True:
            frame = camera.get_frame()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    def video_feed(self):
        """Video streaming route. Put this in the src attribute of an img tag."""
        return Response(self.gen(Camera()),
                        mimetype='multipart/x-mixed-replace; boundary=frame')

    def set_lights(self, value):
        self.actuators.set_all_leds(value, value, value)

    def lights(self):
        if request.form["lights"] == "on":
            self.set_lights(255)
        else:
            self.set_lights(15)
        return '', 200


class NaborisCLI(CommandLine):
    def __init__(self, actuators, sounds, enabled=True):
        super(NaborisCLI, self).__init__("cmdline", False, enabled)
        self.actuators = actuators
        self.sounds = sounds

    def spin_left(self, params):
        value = int(params) if len(params) > 0 else 75
        self.actuators.spin(value)

    def spin_right(self, params):
        value = int(params) if len(params) > 0 else 75
        self.actuators.spin(-value)

    def drive(self, params):
        angle = 0
        speed = 75
        if len(params) > 1:
            values = params.split(" ")

            try:
                if len(values) >= 1:
                    angle = int(values[0])

                if len(values) >= 2:
                    speed = int(values[1])
            except ValueError:
                print("Failed to parse input:", repr(values))
        self.actuators.drive(speed, angle)

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

    def my_exit(self, params):
        self.exit()

    def my_stop(self, params):
        self.actuators.stop()

    def say_hello(self, params):
        self.sounds.play("emotes/hello")
        self.actuators.set_all_leds(0, 0, 15)
        self.actuators.pause(0.1)
        self.actuators.look_straight()
        self.actuators.pause(0.1)
        for _ in range(2):
            self.actuators.look_up()
            self.actuators.pause(0.1)
            self.actuators.look_down()
            self.actuators.pause(0.1)
        self.actuators.look_straight()
        self.actuators.set_all_leds(15, 15, 15)

    def say_alert(self, params):
        self.sounds.play("alert/high_alert")
        self.actuators.set_all_leds(15, 0, 0)
        self.actuators.pause(0.05)
        self.actuators.look_straight()
        for _ in range(3):
            self.actuators.look_left()
            self.actuators.pause(0.1)
            self.actuators.look_right()
            self.actuators.pause(0.1)
        self.actuators.look_straight()
        self.actuators.pause(0.1)
        self.actuators.set_all_leds(15, 15, 15)

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
        )

class Naboris(SerialStream):
    def __init__(self, log=False, enabled=True):
        self.actuators = Actuators()
        super(Naboris, self).__init__("naboris serial", self.actuators, log=log, enabled=enabled)

        self.link_callback(self.actuators, self.receive_actuators)

        self.sounds = SoundStream("sounds", "/home/pi/Music/Bastion/")

    def serial_start(self):
        self.actuators.set_turret(90, 70)
        self.actuators.set_turret(90, 90)
        self.actuators.set_all_leds(15, 15, 15)
        self.actuators.set_battery(4800, 5039)

    def receive_actuators(self, timestamp, packet):
        print(packet)

    def request_battery(self):
        self.actuators.ask_battery()

    def serial_close(self):
        self.actuators.stop()
        self.actuators.release()
