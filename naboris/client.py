from remote.socket_client import NaborisSocketClient, CLI
from remote.logitech import Logitech
from atlasbuggy.robot import Robot

robot = Robot()

socket = NaborisSocketClient()
cli = CLI()
logitech = Logitech()

cli.give(socket=socket)
logitech.give(socket=socket)

robot.run(socket, cli, logitech)
