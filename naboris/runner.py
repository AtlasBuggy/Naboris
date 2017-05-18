
from actuators import Actuators
from naboris_cli import NaborisCLI
from atlasbuggy.datastreams.serialstream import SerialStream
from atlasbuggy.datastreams.iostream.cmdline import CommandLine
from atlasbuggy.robot import Robot

actuators = Actuators()
serial = SerialStream("serial", actuators, log=True, debug=True)
cmdline = NaborisCLI("cmdline", actuators)

naboris = Robot(serial)
naboris.run()
