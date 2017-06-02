
from naboris.client import NaborisSocketClient, CLI
from atlabuggy.robot import Robot

socket = NaborisSocketClient()
cli = CLI(socket)

Robot.run(socket, cli)
