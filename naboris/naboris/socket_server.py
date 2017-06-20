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
        for client in self.client_writers.values():
            if self.camera.frame is not None:
                self.write(client, self.camera.get_bytes_frame(), append_newline=False)
        await asyncio.sleep(1 / self.camera.fps)
