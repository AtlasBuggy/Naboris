from atlasbuggy.filestream.parser import Parser


class SerialFile(Parser):
    def __init__(self, serial_stream, file_name, directory=None, debug=False, start_index=0, end_index=-1):
        super(SerialFile, self).__init__(file_name, directory, debug, start_index, end_index)
        self.serial_stream = serial_stream

    def receive(self, index, packet_type, timestamp, whoiam, packet):
        self.serial_stream.timestamp = timestamp
        self.serial_stream.packet = packet

        if packet_type == "error":
            self.debug_print("%s" % self.serial_stream.packet, ignore_flag=True)

        elif packet_type == "debug":
            self.debug_print("%s" % self.serial_stream.packet)

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

    def update(self):
        self.serial_stream.update()