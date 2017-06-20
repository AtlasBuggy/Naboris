from atlasbuggy.cmdline import CommandLine
from atlasbuggy.website.socket import SocketClient


class NaborisSocketClient(SocketClient):
    def __init__(self, enabled=True):
        super(NaborisSocketClient, self).__init__("naboris cli", "naboris", enabled=enabled)

    async def read(self):
        await self.reader.read(128)

    def received(self, data):
        self.logger.debug(data)


class CLI(CommandLine):
    def __init__(self):
        super(CLI, self).__init__(True)

        self.socket_client = None

    def take(self):
        self.socket_client = self.streams["socket"]

    def handle_input(self, line):
        if line == "q":
            self.socket_client.write_eof()
        else:
            self.socket_client.write(line + "\n")
