from remote.socket_client import NaborisSocketClient, CLI
from remote.logitech import Logitech
from atlasbuggy.robot import Robot

socket = NaborisSocketClient()
cli = CLI()
logitech = Logitech()

robot = Robot(socket, cli, logitech)

cli.give(socket=socket)
logitech.give(socket=socket)

robot.run()