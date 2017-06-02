from atlasbuggy.website.socket import SocketServer


class NaborisSocketServer(SocketServer):
    def __init__(self, cmdline, enabled=True, debug=False):
        super(NaborisSocketServer, self).__init__(enabled, debug)

        self.cmdline = cmdline

    def received(self, writer, data):
        self.cmdline.handle_input()
