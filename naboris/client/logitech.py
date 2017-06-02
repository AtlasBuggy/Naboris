
from atlasbuggy.ui.pygamestream.pygame_joystick import BuggyJoystick


class Logitech(BuggyJoystick):
    def __init__(self, socket):
        super(Logitech, self).__init__(
            ['left x', 'left y', 'right x', 'right y'],
            [0.05, 0.05, 0.05, 0.055],
            ['X', 'A', 'B', 'Y', 'LB', 'RB', 'LT', 'RT', 'back', 'left stick',
             'left stick', 'right stick'],
        )
        self.socket = socket

    def axis_updated(self, name, value):
        if name == "left x":
            if value > 0:
                self.socket.write("l %d" % int(value * 255))
            elif value < 0:
                self.socket.write("r %d" % int(abs(value) * 255))
            else:
                self.socket.write("s")
