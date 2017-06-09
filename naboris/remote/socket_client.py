from atlasbuggy.cmdline import CommandLine
from atlasbuggy.website.socket import SocketClient


class NaborisSocketClient(SocketClient):
    def __init__(self, enabled=True, debug=False):
        super(NaborisSocketClient, self).__init__("naboris cli", "naboris", enabled=enabled, debug=debug)

    def received(self, data):
        print(data)


class CLI(CommandLine):
    def __init__(self, socket_client):
        super(CLI, self).__init__(False, True)

        self.socket_client = socket_client

    def handle_input(self, line):
        if line == "q":
            self.socket_client.write_eof()
        else:
            self.socket_client.write(line + "\n")
