
from atlasbuggy.datastream import DataStream
from atlasbuggy.serialstream.files import Parser
from atlasbuggy.serialstream.object import SerialObject
import asyncio

class SerialFile(DataStream):
    def __init__(self, file_name, directory, serial_stream, debug=False, start=0, end=-1):
        super(SerialFile, self).__init__("serial file", True, debug, False, True)
        self.parser = Parser("serial file", file_name, directory, start, end)
        self.serial_stream = serial_stream
        self.current_index = self.parser.start_index

    def receive_command(self, whoiam, timestamp, packet):
        pass

    def receive_user(self, whoiam, timestamp, packet):
        pass

    def whoiams_equal(self, arg, whoiam):
        if isinstance(arg, SerialObject):
            return arg.whoiam == whoiam
        else:
            return arg == whoiam

    async def run(self):
        while not self.parser.finished:
            result = self.parser.next()
            if result is None:
                continue
            index, packet_type, timestamp, whoiam, packet = result
            self.current_index = index
            self.serial_stream.timestamp = timestamp
            self.serial_stream.packet = packet

            if packet_type == "error" or packet_type == "debug":
                if packet_type == "debug" and self.debug:
                    continue
                print("\t%s" % self.serial_stream.packet)
            elif packet_type == "command":
                self.receive_command(whoiam, timestamp, packet)

            elif packet_type == "user":
                self.receive_user(whoiam, timestamp, packet)

            elif self.serial_stream.timestamp is None:
                self.serial_stream.deliver_first_packet(whoiam, packet)

            else:
                self.serial_stream.deliver(whoiam)
                self.serial_stream.received(whoiam)
                self.serial_stream.update_recurring(timestamp)
        await asyncio.sleep(0.0001)

        # received packets
        # linked callbacks
        # raise errors
        # print debugs
        # receive commands
