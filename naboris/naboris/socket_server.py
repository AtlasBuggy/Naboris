from atlasbuggy.website.socket import SocketServer


class NaborisSocketServer(SocketServer):
    def __init__(self, enabled=True):
        super(NaborisSocketServer, self).__init__(enabled)

        self.cmdline = None

    def take(self):
        self.cmdline = self.streams["cmdline"]

    def received(self, writer, data):
        self.cmdline.handle_input(data)
