
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

        super(Naboris, self).__init__(self.actuators)

    def received(self):
        self.battery_plot.append(self.actuators.value_V)

    def close(self):
        self.plotter.close()

file_name = "16;43;13"
directory = "2017_May_10"
simulator = RobotSimulator(file_name, directory, naboris, debug_enabled=False)
simulator.run()
