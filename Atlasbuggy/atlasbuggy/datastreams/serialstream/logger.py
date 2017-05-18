"""
Contains the Logger class. This class writes incoming packets and their corresponding
whoiam ID and timestamp to a text file. When the program ends, this text file is compressed into a gzip file.
"""

from atlasbuggy.datastreams.filestream import *


class Logger(BaseWriteFile):
    """A class for recording data from a robot to a logs file"""

    def __init__(self, file_name=None, directory=None):
        """
        :param file_name: If None, the current time is used (hh;mm;ss)
        :param directory: If None, today's date is used (YYYY_Mmm_DD).
            If a tuple containing None, None is replaced with today's date
            example: ("some_data", None) -> "some_data/2017_Mar_09"
        """
        file_name, directory = self.format_path_as_time(
            file_name, directory, default_log_file_name, default_log_dir_name
        )
        super(Logger, self).__init__("Serial File Logger", file_name, directory, True, log_file_type, log_dir, enable_dumping=False)

        self.line_code = (("%s" * 6) + "\n")

    def record(self, timestamp, whoiam, packet, packet_type):
        """
        Record incoming packet.

        :param timestamp: time packet arrived. -1 if it's an initialization packet
        :param whoiam: whoiam ID of packet (see object.py for details)
        :param packet: packet received by robot port
        :param packet_type: packet decorator. Determines how the packet was used
        """

        if self.is_open():
            if timestamp is None:  # before interface's start method is called (before robot object's initialize)
                timestamp = no_timestamp
            else:
                assert type(timestamp) == float

            # for error and debug packets, they can be multi-line, replace with continue characters
            if packet_type == "error" or packet_type == "debug":
                if "\n" in packet:
                    packet = packet.replace("\n", "\n" + packet_types[packet_type + " continued"])
                    packet += "\n" + packet_types[packet_type + " end"]
            elif packet == "user":
                packet = packet.replace("\n", "\\n")

            self.write(self.line_code % (
                packet_types[packet_type], timestamp, time_whoiam_sep, whoiam, whoiam_packet_sep, packet))

