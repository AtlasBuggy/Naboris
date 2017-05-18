
from atlasbuggy.datastreams.iostream.cmdline import CommandLine

class NaborisCLI(CommandLine):
    def __init__(self, name, actuators):
        super(NaborisCLI, self).__init__(name, False)
        self.actuators = actuators

    def handle_input(self, line):
        if line == 'q':
            self.exit()
