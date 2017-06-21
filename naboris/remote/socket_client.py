import cv2
import numpy as np
# import asyncio
from atlasbuggy.cmdline import CommandLine
from atlasbuggy.website.socket import SocketClient


class NaborisSocketClient(SocketClient):
    def __init__(self, enabled=True):
        super(NaborisSocketClient, self).__init__("naboris client", "naboris", enabled=enabled)
        self.length = 0
        self.bytes_frame = b''
        self.frame = None

    async def update(self):
        if await self.read(1) == b'\x54':
            self.length = int.from_bytes(await self.read(4), 'big')
            self.bytes_frame = await self.read(self.length)
            self.frame = self.to_image(self.bytes_frame)

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
