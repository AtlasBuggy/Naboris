"""
The RobotObject class acts a container for data received from and sent to the corresponding robot port.
Data is directed using a RobotRunner class. Every robot object has a unique whoiam ID which is
also defined on the microcontroller.
"""

from atlasbuggy.serial.objects import SerialObject
from atlasbuggy.serial.clock import CommandPause


class Microcontroller(SerialObject):
    def __init__(self, whoiam, enabled=True, baud=None):
        """
        A container for data received from the corresponding microcontroller.

        Make sure the whoiam ID corresponds to the one defined on the microcontroller
        (see templates for details).

        Define object variables here

        :param whoiam: a unique string ID containing ascii characters
        :param enabled: disable or enable object
        """
        self.whoiam = whoiam
        self._pause_command = None
        super(Microcontroller, self).__init__(enabled, baud)

    def receive_first(self, packet):
        """
        Override this method when subclassing RobotObject if you're expecting initial data

        Initialize any data defined in __init__ here.
        If the initialization packet is not an empty string, it's passed here. Otherwise, this method isn't called

        :param packet: The first packet received by the robot object's port
        :return: a string if the program needs to exit ("done" or "error"), None if everything is ok
        """
        raise NotImplementedError("Please override this method when subclassing Microcontroller")

    def pause(self, gap_time):
        """
        Non-blocking pause for sending commands. When the serial async loop encounters this,
        it will keep checking back until the timer has expired then move to the next command for the object
        """
        if self.enabled and self.is_live:
            self.command_packets.put(CommandPause(gap_time))

    def __str__(self):
        return "%s(whoiam=%s)\n\t" % (self.__class__.__name__, self.whoiam)
