import asyncio
from atlasbuggy.files import *


class Parser(BaseReadFile):
    """
    A class for parsing logs files and returning their data nicely.

    This class is meant to be used as an iterator.

    for example:
    parser = Parser("file name", "directory in logs")
    for index, timestamp, whoiam, packet in parser:
        pass

    Parser returns data in the order that it was recorded. If, say, an IMU
    sensor recorded three times and then a GPS recorded once, the parser would
    return the IMU's data three times and then the GPS last
    """

    def __init__(self, file_name, directory=None, enabled=True, debug=False, start_index=0, end_index=-1):
        """
        :param file_name: name to search for
            can be part of the name. If the desired file is named
                "15;19;32.gzip", input_name can be "15;19"
        :param directory: searches in working directory. (must be exact name of the folder)
            If None, the most recently created folder will be used
        :param start_index: line number to start the log file from
        :param end_index: line number to end the log file on
        """
        super(Parser, self).__init__(file_name, directory, True, log_file_type, log_dir, enabled, debug,
                                     False, True)
        if self.enabled:
            self.open()
            self.contents = self.contents.split("\n")
        else:
            self.contents = ""

        # index variables
        self.start_index = start_index
        self.end_index = end_index
        self.index = 0  # current packet number (or line number)
        self.finished = False

        if self.end_index == -1:
            self.end_index = len(self.contents)

    def receive_command(self, whoiam, timestamp, packet):
        pass

    def receive_user(self, whoiam, timestamp, packet):
        pass

    def receive_debug(self, whoiam, timestamp, packet):
        pass

    def receive_error(self, whoiam, timestamp, packet):
        pass

    def receive_object(self, whoiam, timestamp, packet):
        pass

    def receive_first(self, whoiam, packet):
        pass

    async def run(self):
        if self.enabled:
            while self.next():
                await self.update()

                # received packets
                # linked callbacks
                # raise errors
                # print debugs
                # receive commands

            self.file_finished()

    async def update(self):
        await asyncio.sleep(0.0)

    def file_finished(self):
        pass

    def receive(self, index, packet_type, timestamp, whoiam, packet):
        pass

    def _receive(self, index, packet_type, timestamp, whoiam, packet):
        self.receive(index, packet_type, timestamp, whoiam, packet)

        if packet_type == "error":
            self.debug_print("%s" % packet, ignore_flag=True)
            self.receive_error(whoiam, timestamp, packet)

        elif packet_type == "debug":
            self.debug_print("%s" % packet)
            self.receive_debug(whoiam, timestamp, packet)

        elif packet_type == "command":
            self.receive_command(whoiam, timestamp, packet)

        elif packet_type == "user":
            self.receive_user(whoiam, timestamp, packet)

        elif self.start_time is None:
            self.receive_first(whoiam, packet)

        else:
            self.receive_object(whoiam, timestamp, packet)

    def next(self):
        """
        While self.content_index hasn't reached the end of the file, parse the current line
        and return the contents. If the line wasn't parsed correctly, StopIteration is raised.
        :return: tuple: (index # (int), timestamp (float), whoiam (string), packet (string))
        """
        if self.index < self.end_index:
            line = self.parse_line()
            self.index += 1

            if line is not None:
                packet_type, timestamp, whoiam, packet = line
                self._receive(self.index - 1, packet_type, timestamp, whoiam, packet)
                return True
        return False

    def parse_line(self):
        """
        Parse the current line using self.content_index and separator globals (e.g. time_whoiam_sep).
        Return the contents found
        :return: timestamp, whoiam, packet; None if the line was parsed incorrectly
        """
        line = self.contents[self.index]

        if len(line) == 0:
            # print("Empty line (line #%s)" % self.index)
            return None
        if line[0] not in packet_types.keys():
            # print("Invalid packet type: '%s' in line #%s: %s" % (line[0], self.index, line))
            return None
        packet_type = packet_types[line[0]]

        whoiam = ""
        packet = ""

        timestamp = no_timestamp  # no timestamp by default

        # the values are from the end of the name to the end of the line
        if len(packet_type) >= len("error") and packet_type[:len("error")] == "error":
            if len(packet_type) == len("error"):
                # parse error packet
                timestamp, time_index, whoiam, whoiam_index = self.find_packet_header(line)
                if timestamp == no_timestamp:
                    timestamp = 0.0

                # format error message for printing
                packet = "\n----- Error message in log (time: %0.4fs, type: %s) -----\n" % (
                    timestamp, whoiam)
                packet += "Traceback (most recent call last):\n"
                packet += line[whoiam_index + len(time_whoiam_sep):]

            elif packet_type[len("error") + 1:] == "continued":
                # error message continued on next line, add to the current message
                packet = line[1:]

            elif packet_type[len("error") + 1:] == "end":
                # error message end, add end flag
                packet = "----- End error message -----\n"

            packet_type = "error"  # the user shouldn't use continue or end packet types

        elif len(packet_type) >= len("debug") and packet_type[:len("debug")] == "debug":
            if len(packet_type) == len("debug"):
                # parse debug packet
                timestamp, time_index, whoiam, whoiam_index = self.find_packet_header(line)
                packet += line[whoiam_index + len(time_whoiam_sep):]

            elif packet_type[len("debug") + 1:] == "continued":
                # debug message continued on next line, add to the current message
                packet = "\n" + line[1:]

            elif packet_type[len("debug") + 1:] == "end":
                # debug message end, add end flag (if multi-line)
                packet = "[end debug from %s]: " % line[1:]

            packet_type = "debug"  # the user shouldn't use continue or end packet types

        else:  # parse object, command, and user packets
            timestamp, time_index, whoiam, whoiam_index = self.find_packet_header(line)
            if timestamp == "invalid":
                print("Invalid timestamp in line #%s: %s" % (self.index, line))
                return None
            if len(whoiam) == 0:
                print("Invalid whoiam in line #%s: %s" % (self.index, line))
                return None

            # packet is from the end of the timestamp marker to the end
            packet = line[whoiam_index + len(time_whoiam_sep):]
            if packet_type == "user":
                packet.replace("\\n", "\n")

        if timestamp == no_timestamp:
            timestamp = None
        else:  # go through initialization packets, then jump to start index
            if self.index < self.start_index:
                self.index = self.start_index

        return packet_type, timestamp, whoiam, packet

    def find_packet_header(self, line):
        # search for the timestamp from the current index to the end of the line
        time_index = line.find(time_whoiam_sep)

        # search for the name from the current index to the end of the line
        whoiam_index = line.find(whoiam_packet_sep)

        if time_index != -1:  # if timestamp was found
            timestamp = line[1:time_index]
            if timestamp != no_timestamp:
                # attempt to convert to float
                try:
                    timestamp = float(timestamp)
                except ValueError:
                    # print("Invalid timestamp:", timestamp)
                    timestamp = "invalid"
        else:
            timestamp = "invalid"

        if whoiam_index != -1:  # if whoiam was found
            # the name is from the end of the timestamp to name_index
            whoiam = line[time_index + len(time_whoiam_sep): whoiam_index]
        else:
            whoiam = ""

        if type(timestamp) == float:
            if self.start_time is None:
                self.start_time = timestamp
            else:
                self.timestamp = timestamp

        return timestamp, time_index, whoiam, whoiam_index
