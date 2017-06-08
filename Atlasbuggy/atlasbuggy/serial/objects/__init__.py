
from multiprocessing import Queue


class SerialObject:
    def __init__(self, enabled=True, baud=None, port_class=None):
        """
        A container for data received from the corresponding microcontroller.

        Make sure the whoiam ID corresponds to the one defined on the microcontroller
        (see templates for details).

        Define object variables here

        :param whoiam: a unique string ID containing ascii characters
        :param enabled: disable or enable object
        """
        self.enabled = enabled
        self.baud = baud
        self.is_live = False
        self.port_class = port_class
        self.command_packets = Queue(maxsize=255)

    def receive(self, timestamp, packet):
        """
        Override this method when subclassing RobotObject

        Parse incoming packets received by the corresponding port.
        I would recommend ONLY parsing packets here and not doing anything else.

        :param timestamp: The time the packet arrived
        :param packet: A packet (string) received from the robot object's port
        :return: a string if the program needs to exit ("done" or "error"), None if everything is ok
        """
        raise NotImplementedError("Please override this method when subclassing ")

    def send(self, packet):
        """
        Do NOT override this method when subclassing RobotObject

        Queue a new packet for sending. The packet end (\n) will automatically be appended

        :param packet: A packet (string) to send to the microcontroller without the packet end character
        """
        if self.enabled and self.is_live:
            self.command_packets.put(packet)

    def __str__(self):
        return "%s()\n\t" % self.__class__.__name__
