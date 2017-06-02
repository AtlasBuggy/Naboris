from atlasbuggy.serial.object import SerialObject


class Actuators(SerialObject):
    def __init__(self, enabled=True):
        self.num_leds = None
        self.speed_increment = None
        self.speed_delay = None
        self.lower_V = None
        self.upper_V = None
        self.percentage_V = None
        self.value_V = None
        self.turret_yaw = 90
        self.turret_azimuth = 90
        self.led_states = None

        super(Actuators, self).__init__("naboris actuators", enabled)

    def receive_first(self, packet):
        data = packet.split("\t")
        assert len(data) == 7

        self.num_leds = int(data[0])
        self.speed_increment = int(data[1])
        self.speed_delay = int(data[2])
        self.lower_V = int(data[3])
        self.upper_V = int(data[4])
        self.percentage_V = int(data[5])
        self.value_V = int(data[6])
        self.led_states = [[0, 0, 0] for _ in range(self.num_leds)]

    def receive(self, timestamp, packet):
        if packet[0] == 'b':
            data = packet[1:].split('\t')
            self.value_V = int(data[0])
            self.percentage_V = int(data[1])
            # print("Battery: %s%%, %s mV" % (self.percentage_V, self.value_V))

    def drive(self, speed, angle):
        command = "p%d%03d%03d" % (int(-speed > 0), angle, abs(speed))

        self.send(command)

    def spin(self, speed):
        command = "r%d%03d" % (int(-speed > 0), abs(speed))
        self.send(command)

    def stop(self):
        self.send("h")

    def release(self):
        self.send("d")

    def set_turret(self, yaw, azimuth):
        if azimuth < 30:
            azimuth = 30
        if azimuth > 100:
            azimuth = 100

        if yaw < 30:
            yaw = 30
        if yaw > 150:
            yaw = 150

        self.send("c%03d%03d" % (yaw, azimuth))

    def set_yaw(self, yaw):
        self.turret_yaw = yaw
        self.set_turret(self.turret_yaw, self.turret_azimuth)

    def set_azimuth(self, azimuth):
        self.turret_azimuth = azimuth
        self.set_turret(self.turret_yaw, self.turret_azimuth)

    def look_up(self, azimuth=70):
        self.set_azimuth(azimuth)

    def look_down(self, azimuth=100):
        self.set_azimuth(azimuth)

    def look_left(self, yaw=110):
        self.set_yaw(yaw)

    def look_right(self, yaw=70):
        self.set_yaw(yaw)

    def look_straight(self):
        self.turret_yaw = 90
        self.turret_azimuth = 90
        self.set_turret(self.turret_yaw, self.turret_azimuth)

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

    def set_led(self, led_index, *rgb, show=True):
        r, g, b = self.constrain_input(rgb)
        led_index = int(abs(led_index))
        if led_index >= self.num_leds:
            led_index = self.num_leds - 1
        if led_index < 0:
            led_index = 0

        self.led_states[led_index][0] = r
        self.led_states[led_index][1] = g
        self.led_states[led_index][2] = b

        self.send("o%03d%03d%03d%03d" % (led_index, r, g, b))
        if show:
            self.show()

    def set_leds(self, start, end, *rgb, show=True):
        r, g, b = self.constrain_input(rgb)
        start = int(abs(start))
        end = int(abs(end))
        if start >= self.num_leds:
            start = self.num_leds - 1
        if start < 0:
            start = 0

        if end > self.num_leds:
            end = self.num_leds
        if end < 1:
            end = 1

        for index in range(start, end):
            self.led_states[index][0] = r
            self.led_states[index][1] = g
            self.led_states[index][2] = b

        assert end <= self.num_leds and 0 <= start and start < end

        self.send("o%03d%03d%03d%03d%03d" % (start, r, g, b, end))
        if show:
            self.show()

    def set_all_leds(self, *rgb, show=True):
        self.set_leds(0, self.num_leds, rgb, show=show)

    def get_led(self, index):
        return tuple(self.led_states[index])

    def toggle_led_cycle(self):
        self.send("o")

    def show(self):
        self.send("x")

    def ask_battery(self):
        self.send("b")

    def set_battery(self, lower_V, upper_V):
        self.send("b%03d%03d" % (lower_V, upper_V))
