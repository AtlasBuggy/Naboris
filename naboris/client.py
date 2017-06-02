from naboris_client.socket_client import NaborisSocketClient, CLI
from naboris_client.logitech import Logitech
from atlasbuggy.robot import Robot

socket = NaborisSocketClient(debug=True)
cli = CLI(socket)
logitech = Logitech(socket)

Robot.run(socket, cli, logitech)
