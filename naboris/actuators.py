from atlasbuggy.robot.object import RobotObject

class Actuators(RobotObject):
    def __init__(self, enabled=True):
        super(Actuators, self).__init__("naboris actuators", enabled)

    def receive_first(self, packet):
        pass

    def receive(self, timestamp, packet):
        pass

    def drive(self, angle, speed, for_ms=None):
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

    def set_turret(self, yaw, azimuth):
        self.send("c%03d%03d" % (yaw, azimuth))
