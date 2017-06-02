from atlasbuggy.website.socket import SocketServer
from atlasbuggy.robot import Robot


class SocketTest(SocketServer):
    def __init__(self):
        super(SocketTest, self).__init__(debug=True)

    def received(self, writer, data):
        self.write(writer, "ECHO: %s" % data)


socket = SocketTest()

Robot.run(socket)
