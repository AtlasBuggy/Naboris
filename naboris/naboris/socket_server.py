from atlasbuggy.website.socket import SocketServer


class NaborisSocketServer(SocketServer):
    def __init__(self, enabled=True, log_level=None):
        super(NaborisSocketServer, self).__init__(enabled, log_level=log_level)

        self.cmdline = None

    def take(self):
        self.cmdline = self.streams["cmdline"]

    def received(self, writer, data):
        self.cmdline.handle_input(data)
