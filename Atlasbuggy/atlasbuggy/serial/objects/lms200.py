
from atlasbuggy.serial.objects import SerialObject

class LMS200(SerialObject):
    def __init__(self, enabled=True, baud=9600):
        """
        A container for data received from the corresponding microcontroller.

        Make sure the whoiam ID corresponds to the one defined on the microcontroller
        (see templates for details).

        Define object variables here

        :param whoiam: a unique string ID containing ascii characters
        :param enabled: disable or enable object
        """
        super(LMS200, self).__init__(enabled, baud)
