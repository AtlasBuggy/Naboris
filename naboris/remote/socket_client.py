import cv2
import numpy as np
# import asyncio
from atlasbuggy.cmdline import CommandLine
from atlasbuggy.website.socket import SocketClient


class NaborisSocketClient(SocketClient):
    def __init__(self, enabled=True):
        super(NaborisSocketClient, self).__init__("naboris cli", "naboris", enabled=enabled)
        self.buffer = b''
        self.current_index = 0
        self.length = 0
        self.bytes_frame = b''

        self.frame = None

    def read(self):
        return self.reader.read(128)

    def get(self, n):
        incoming = self.buffer[self.current_index: self.current_index + n]
        self.current_index += n
        if self.current_index >= len(self.buffer):
            self.current_index = len(self.buffer) - 1
            return incoming, False
        else:
            return incoming, True

    def clear_buffer(self):
        self.buffer = self.buffer[self.current_index:]

    def update(self):
        incoming, status = self.get(1)
        if status and incoming == 0x54:
            incoming, status = self.get(4)
            if status:
                self.length = int.from_bytes(incoming, 'big')
                incoming, status = self.get(self.length)
                self.bytes_frame += incoming
                if status:
                    self.clear_buffer()
                    self.frame = self.to_image(incoming)

    def to_image(self, byte_stream):
        return cv2.imdecode(np.fromstring(byte_stream, dtype=np.uint8), 1)


class CLI(CommandLine):
    def __init__(self):
        super(CLI, self).__init__(True)

        self.socket_client = None

    def take(self):
        self.socket_client = self.streams["socket"]

    def handle_input(self, line):
        if line == "q":
            self.socket_client.write_eof()
        else:
            self.socket_client.write(line + "\n")
