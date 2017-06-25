import cv2
import numpy as np
import asyncio
from atlasbuggy.cmdline import CommandLine
from atlasbuggy.website.socket import SocketClient


class NaborisSocketClient(SocketClient):
    def __init__(self, enabled=True):
        super(NaborisSocketClient, self).__init__("naboris client", "naboris", enabled=enabled)
        self.bytes_frame = b''
        self.frame = None

    async def update(self):
        if await self.read(1) == b'\x54':
            length = int.from_bytes(await self.read(4), 'big')
            self.bytes_frame = await self.read(length)
            self.frame = self.to_image(self.bytes_frame)

    async def read(self, n=1):
        if self.timeout is not None:
            data = await asyncio.wait_for(self.reader.readexactly(n), timeout=self.timeout)
        else:
            data = await self.reader.readexactly(n)

        if data is None or len(data) == 0:
            self.logger.warning("socket received nothing")
            self.exit()
        return data

    def to_image(self, byte_stream):
        return cv2.imdecode(np.fromstring(byte_stream, dtype=np.uint8), 1)


class CLI(CommandLine):
    def __init__(self):
        super(CLI, self).__init__(True)

        self.socket_client = None

    def take(self, subscriptions):
        self.socket_client = self.subscriptions["socket"].stream

    def handle_input(self, line):
        if line == "q":
            self.socket_client.write_eof()
        else:
            self.socket_client.write(line + "\n")
