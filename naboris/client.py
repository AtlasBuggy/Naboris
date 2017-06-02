
from naboris.socket_client import NaborisSocketClient, CLI
from atlasbuggy.robot import Robot

socket = NaborisSocketClient(debug=True)
cli = CLI(socket)

Robot.run(socket, cli)
