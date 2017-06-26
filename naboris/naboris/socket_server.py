import asyncio
from atlasbuggy.website.socket import SocketServer
from atlasbuggy.subscriptions import Update


class NaborisSocketServer(SocketServer):
    def __init__(self, enabled=True, log_level=None):
        super(NaborisSocketServer, self).__init__(enabled, log_level=log_level)

        self.cmdline = None
        self.camera = None

        self.camera_feed = None
        self.camera_subscription = None

        self.cmdline_tag = "cmdline"
        self.camera_tag = "camera"
        self.require_subscription(self.cmdline_tag)
        self.require_subscription(self.camera_tag, Update)

    def take(self, subscriptions):
        self.camera_subscription = subscriptions[self.camera_tag]

        self.cmdline = subscriptions[self.cmdline_tag].stream
        self.camera = subscriptions[self.camera_tag].stream

        self.camera_feed = subscriptions[self.camera_tag].queue

    def received(self, writer, name, data):
        self.cmdline.handle_input(data)

    async def update(self):
        if len(self.client_writers) > 0:
            while not self.camera_feed.empty():
                frame = self.camera_feed.get()
                bytes_frame = self.camera.numpy_to_bytes(frame)
                length = len(bytes_frame).to_bytes(4, 'big')
                preamble = b'\x54'
                message = preamble + length + bytes_frame
                self.write_all(message, append_newline=False)
        await asyncio.sleep(1 / self.camera.fps)
    
    # def client_connected(self, name):
    #     self.camera_subscription.enabled = True
    #
    # def client_disconnected(self):
    #     if len(self.client_writers) == 0:
    #         self.camera_subscription.enabled = False
