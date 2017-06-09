from atlasbuggy.website.socket import SocketServer


class NaborisSocketServer(SocketServer):
    def __init__(self, enabled=True, debug=False):
        super(NaborisSocketServer, self).__init__(enabled, debug)

        self.cmdline = None

    def take(self):
        self.cmdline = self.streams["cmdline"]

    def received(self, writer, data):
        self.cmdline.handle_input(data)
