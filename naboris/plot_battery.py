from actuators import Actuators

from atlasbuggy.interface.simulated import RobotSimulator
from atlasbuggy.robot import Robot

from atlasbuggy.plotters.collection import RobotPlotCollection
from atlasbuggy.plotters.plot import RobotPlot

from atlasbuggy.plotters.staticplotter import StaticPlotter

class BatteryPlotter(Robot):
    def __init__(self):
        self.actuators = Actuators()

        self.battery_plot = RobotPlot("Battery plot")
        self.plotter = StaticPlotter(1, self.battery_plot)

        super(BatteryPlotter, self).__init__(self.actuators)

    def received(self, timestamp, whoiam, packet, packet_type):
        self.battery_plot.append(self.dt(), self.actuators.value_V)

    def close(self, reason):
        self.plotter.close()

battery_plotter = BatteryPlotter()

file_name = "16;43;13"
directory = "2017_May_10"
simulator = RobotSimulator(file_name, directory, battery_plotter, debug_enabled=True)
simulator.run()
