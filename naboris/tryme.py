import asyncio
from atlasbuggy.logparser import LogParser
from atlasbuggy.robot import Robot
from atlasbuggy.plotters.liveplotter import LivePlotter
from naboris import Naboris


class Simulator(LogParser):
    def __init__(self, file_name, directory, enabled=True, log_level=None):
        super(Simulator, self).__init__(file_name, directory, enabled, log_level=log_level)
        self.naboris = None

    def take(self):
        self.naboris = self.streams["naboris"]

    async def update(self):
        await asyncio.sleep(0.001)

robot = Robot()

simulator = Simulator("21;25;23.log.xz", "logs/2017_Jun_10")
naboris = Naboris(plot=True)
plotter = LivePlotter(1, enabled=naboris.should_plot, exit_all=True)

simulator.give(naboris=naboris)
naboris.give(plotter=plotter)

robot.run(simulator, plotter)
