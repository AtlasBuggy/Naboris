import asyncio
from atlasbuggy.website.socket import SocketServer
from atlasbuggy.subscriptions import Feed


class NaborisSocketServer(SocketServer):
    def __init__(self, enabled=True, log_level=None):
        super(NaborisSocketServer, self).__init__(enabled, log_level=log_level)

        self.cmdline = None
        self.camera = None

        self.camera_feed = None

        self.cmdline_tag = "cmdline"
        self.camera_tag = "camera"
        self.require_subscription(self.cmdline_tag)
        self.require_subscription(self.camera_tag, Feed)

    def take(self, subscriptions):
        self.cmdline = subscriptions[self.cmdline_tag].stream
        self.camera = subscriptions[self.camera_tag].stream

        self.camera_feed = subscriptions[self.camera_tag].queue

    def received(self, writer, name, data):
        self.cmdline.handle_input(data)

    async def update(self):
        if len(self.client_writers) > 0:
            while not self.camera_feed.empty():
                output = self.camera_feed.get()
                if len(output) == 2:
                    frame, bytes_frame = output
                    length = len(bytes_frame).to_bytes(4, 'big')
                    preamble = b'\x54'
                    message = preamble + length + bytes_frame
                    self.write_all(message, append_newline=False)
                else:
                    self.camera.post_bytes = True
        await asyncio.sleep(1 / self.camera.fps)
