from actuators import Actuators
from atlasbuggy.serialstream import SerialStream
from atlasbuggy.iostream.cmdline import CommandLine


class NaborisCLI(CommandLine):
    def __init__(self, actuators, enabled=True):
        super(NaborisCLI, self).__init__("cmdline", False, enabled)
        self.actuators = actuators

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
                self.actuators.look_up(100)
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

    def check_commands(self, line, **commands):
        function = None
        current_command = ""
        for command, fn in commands.items():
            if line.startswith(command) and len(command) > len(current_command):
                function = fn
                current_command = command
        if function is not None:
            print(line, current_command, repr(line[len(current_command):]))
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
            battery=self.battery
        )

class Naboris(SerialStream):
    def __init__(self, log=False, enabled=True):
        self.actuators = Actuators()
        super(Naboris, self).__init__("naboris serial", self.actuators, log=log, enabled=enabled)

        self.link_callback(self.actuators, self.receive_actuators)

    def start(self):
        self.actuators.set_turret(90, 70)
        self.actuators.set_turret(90, 90)
        self.actuators.set_all_leds(15, 15, 15)
        self.actuators.set_battery(4800, 5039)

    def receive_actuators(self, timestamp, packet):
        print(packet)

    def request_battery(self):
        self.actuators.ask_battery()

    def close(self):
        self.actuators.stop()
        self.actuators.release()
