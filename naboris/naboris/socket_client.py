from atlasbuggy.website.socket import SocketClient


class NaborisSocketClient(SocketClient):
    def __init__(self, enabled=True, debug=False):
        super(NaborisSocketClient, self).__init__("naboris cli", enabled, debug)

    def received(self, data):
        print(data)
