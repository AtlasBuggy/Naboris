from atlasbuggy.website.socket import SocketClient
from atlasbuggy.ui.cmdline import CommandLine
from atlasbuggy.robot import Robot


class CLI(CommandLine):
    def __init__(self, socket_client):
        super(CLI, self).__init__(False, True)

        self.socket_client = socket_client

    def handle_input(self, line):
        if line == "eof":
            self.socket_client.write_eof()
        else:
            self.socket_client.write(line + "\n")


class SocketTest(SocketClient):
    def __init__(self):
        super(SocketTest, self).__init__("socket test")

    def received(self, data):
        print(data)

socket = SocketTest()

Robot.run(CLI(socket), socket)
