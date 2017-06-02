import math
from atlasbuggy.ui.pygamestream.pygame_joystick import BuggyJoystick


class Logitech(BuggyJoystick):
    def __init__(self, socket):
        super(Logitech, self).__init__(
            ['left x', 'left y', 'right x', 'right y'],
            [0.2, 0.2, 0.2, 0.2],
            ['X', 'A', 'B', 'Y', 'LB', 'RB', 'LT', 'RT', 'back', 'left stick',
             'left stick', 'right stick'],
        )
        self.socket = socket

    def update(self):
        value = self.get_axis("right x")
        if value != 0:
            self.spin(int(128 * value))

        value = self.get_axis("right y")
        if value != 0:
            if value > 0:
                self.drive(180, int(value * 255))
            elif value < 0:
                self.drive(0, int(abs(value) * 255))

        if self.dpad[0] != 0 or self.dpad[1] != 0:
            self.drive(math.degrees(math.atan2(-self.dpad[0], self.dpad[1])), 255)

    def dpad_updated(self, value):
        if value[0] == 0 and value[1] == 0:
            self.stop()

    def axis_updated(self, name, value):
        if name == "right x" or name == "right y":
            if value == 0:
                self.stop()

        elif name == "left x" or name == "left y":
            yaw = int(-90 * self.get_axis("left x") + 90)
            azimuth = int(90 * self.get_axis("left y") + 90)
            self.look(yaw, azimuth)

    def look(self, yaw, azimuth):
        self.socket.write("look %d %d" % (yaw, azimuth))

    def drive(self, angle, speed):
        self.socket.write("d %d %d" % (angle, speed))

    def spin(self, speed):
        if speed > 0:
            self.socket.write("r %d" % speed)
        elif speed < 0:
            self.socket.write("l %d" % abs(speed))
        else:
            self.stop()

    def stop(self):
        self.socket.write("s")
