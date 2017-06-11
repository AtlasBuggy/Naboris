from atlasbuggy.logparser import LogParser


class SerialFile(LogParser):
    def __init__(self, file_name, directory=None, enabled=True, log_level=None, ):
        super(SerialFile, self).__init__(file_name, directory, enabled, log_level)

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
