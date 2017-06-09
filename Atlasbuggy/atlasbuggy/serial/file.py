from atlasbuggy.files.parser import Parser


class SerialFile(Parser):
    def __init__(self, serial_stream, file_name, directory=None, debug=False, start_index=0, end_index=-1):
        super(SerialFile, self).__init__(file_name, directory, debug, start_index, end_index)
        self.serial_stream = serial_stream

    def start(self):
        self.start_time = None
        self.serial_start()

    def serial_start(self):
        pass

    def receive(self, index, packet_type, timestamp, whoiam, packet):
        self.serial_stream.timestamp = timestamp
        self.serial_stream.packet = packet

        if self.serial_stream.timestamp is None:
            self.serial_stream.deliver_first_packet(whoiam, packet)
        else:
            self.serial_stream.deliver(whoiam)
            self.serial_stream.received(whoiam)
            self.serial_stream.update_recurring(timestamp)
