import asyncio
from atlasbuggy.website.socket import SocketServer


class NaborisSocketServer(SocketServer):
    def __init__(self, enabled=True, log_level=None):
        super(NaborisSocketServer, self).__init__(enabled, log_level=log_level)

        self.cmdline = None
        self.camera = None

    def take(self):
        self.cmdline = self.streams["cmdline"]
        self.camera = self.streams["camera"]

    def received(self, writer, name, data):
        self.cmdline.handle_input(data)

    async def update(self):
        if len(self.client_writers) > 0:
            if self.camera.frame is not None:
                bytes_frame = self.camera.get_bytes_frame()
                length = len(bytes_frame).to_bytes(4, 'big')
                preamble = b'\x54'
                message = preamble + length + bytes_frame
                self.write_all(message, append_newline=False)
        await asyncio.sleep(1 / self.camera.fps)
