from atlasbuggy.robot.object import RobotObject

class Actuators(RobotObject):
    def __init__(self, enabled=True):
        self.num_leds = None
        self.speed_increment = None
        self.speed_delay = None
        super(Actuators, self).__init__("naboris actuators", enabled)

    def receive_first(self, packet):
        data = packet.split("\t")
        assert len(data) == 3

        self.num_leds = data[0]
        self.speed_increment = data[1]
        self.speed_delay = data[2]

    def receive(self, timestamp, packet):
        pass

    def drive(self, speed, angle, for_ms=None):
        command = "p%d%03d%03d" % (int(-speed > 0), angle, abs(speed))
        if for_ms is not None:
            command += str(int(for_ms))

        self.send(command)

    def spin(self, speed, for_ms=None):
        command = "r%d%03d" % (int(-speed > 0), abs(speed))
        if for_ms is not None:
            command += str(int(for_ms))
        self.send(command)

    def stop(self):
        self.send("h")

    def release(self):
        self.send("d")

    def do_circle(self):
        self.send("x")

    def set_turret(self, yaw, azimuth):
        self.send("c%03d%03d" % (yaw, azimuth))

    @staticmethod
    def constrain_value(value):
        if value < 0:
            value = 0
        if value > 255:
            value = 255
        return value

    def constrain_input(self, rgb):
        if len(rgb) == 1:
            rgb = rgb[0]
        return list(map(self.constrain_value, rgb))

    def set_led(self, num_leds, *rgb):
        r, g, b = self.constrain_input(rgb)
        num_leds = int(abs(num_leds))
        self.send("o%03d%03d%03d%03d" % (num_leds, r, g, b))

    def set_leds(self, start, end, *rgb):
        r, g, b = self.constrain_input(rgb)
        start = int(abs(start))
        end = int(abs(end))

        assert end <= self.num_leds and 0 <= start and start < end

        self.send("o%3.0d%3.0d%3.0d%3.0d%3.0d" % (start, r, g, b, end))

    def set_all_leds(self, *rgb):
        self.set_leds(0, self.num_leds, rgb)

    def show(self):
        self.send("x")
