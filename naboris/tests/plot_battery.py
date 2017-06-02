from atlasbuggy.interface.simulated import RobotSimulator
from atlasbuggy.plotters.plot import RobotPlot
from atlasbuggy.plotters.staticplotter import StaticPlotter

from atlasbuggy.robot import Robot
from naboris.actuators import Actuators


class BatteryPlotter(Robot):
    def __init__(self):
        self.actuators = Actuators()

        self.battery_plot = RobotPlot("Battery plot")
        self.plotter = StaticPlotter(1, self.battery_plot)

        super(BatteryPlotter, self).__init__(self.actuators)

    def received(self, timestamp, whoiam, packet, packet_type):
        self.battery_plot.append(self.dt(), self.actuators.value_V)

    def close(self, reason):
        print(sum(self.battery_plot.data[1]) / len(self.battery_plot.data[1]))
        self.plotter.close()

battery_plotter = BatteryPlotter()

file_name = "16;42;39"
directory = "2017_May_10"
simulator = RobotSimulator(file_name, directory, battery_plotter, debug_enabled=True)
simulator.run()
