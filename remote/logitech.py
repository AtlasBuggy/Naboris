import math

from atlasbuggy.pygamestream.pygame_joystick import BuggyJoystick


class Logitech(BuggyJoystick):
    def __init__(self, enabled=True, log_level=None):
        super(Logitech, self).__init__(
            ['left x', 'left y', 'right x', 'right y'],
            [0.2, 0.2, 0.2, -0.2],
            ['X', 'A', 'B', 'Y', 'LB', 'RB', 'LT', 'RT', 'back', 'left stick',
             'left stick', 'right stick'], enabled=enabled, log_level=log_level
        )
        self.light_toggle = False
        self.socket = None
        self.max_speed = 255

    def take(self, subscriptions):
        self.socket = subscriptions["socket"].stream

    def update(self):
        # if value != 0:
        #     self.spin(int(128 * value))

        x_value = self.get_axis("right x")
        y_value = self.get_axis("right y")
        spin_value = self.get_axis("left x")
        if x_value != 0 or y_value != 0 or spin_value != 0:
            angle = int(math.degrees(math.atan2(x_value, -y_value))) + 180
            speed = int(self.max_speed * math.sqrt(x_value ** 2 + y_value ** 2))
            angular = int(self.max_speed / 2 * spin_value)
            self.drive(angle, speed, angular)

        # if self.dpad[0] != 0 or self.dpad[1] != 0:
        #     self.drive(math.degrees(math.atan2(-self.dpad[0], self.dpad[1])), self.max_speed, 0)

    def dpad_updated(self, value):
        # if value[0] == 0 and value[1] == 0:
        #     self.stop()
        if value[0] == 1:
            yaw = 70
        elif value[0] == -1:
            yaw = 110
        else:
            yaw = 90

        if value[1] == 1:
            azimuth = 70
        elif value[1] == -1:
            azimuth = 100
        else:
            azimuth = 90

        self.look(yaw, azimuth)

    def axis_updated(self, name, value):
        if name == "right x" or name == "right y" or name == "left x":
            if value == 0:
                self.stop()

    def button_updated(self, name, value):
        if name == "RB":
            self.socket.write("sound")
        elif name == "LB" and value:
            if self.light_toggle:
                self.lights(15)
            else:
                self.lights(255)
            self.light_toggle = not self.light_toggle

    def lights(self, value):
        self.socket.write("white %d" % value)

    def look_straight(self):
        self.socket.write("look")

    def look(self, yaw, azimuth):
        self.socket.write("look %d %d" % (yaw, azimuth))

    def drive(self, angle, speed, angular):
        self.socket.write("d %d %d %d" % (angle, speed, angular))

    def spin(self, speed):
        if speed > 0:
            self.socket.write("r %d" % speed)
        elif speed < 0:
            self.socket.write("l %d" % abs(speed))
        else:
            self.stop()

    def stop(self):
        self.socket.write("s")
