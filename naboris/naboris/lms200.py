
from atlasbuggy.serial import SerialStream
from atlasbuggy.serial.objects.lms200 import LMS200


class LMS200stream(SerialStream):
    def __init__(self):
        self.lms200 = LMS200()
        super(LMS200stream, self).__init__(self.lms200)

    def serial_start(self):
        pass

    def update(self):
        pass

    def serial_close(self):
        pass
