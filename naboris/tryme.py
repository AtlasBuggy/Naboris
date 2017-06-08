from atlasbuggy.robot import Robot
from atlasbuggy.ui.plotters.liveplotter import LivePlotter
# from atlasbuggy.ui.plotters.staticplotter import StaticPlotter
from naboris import Naboris
from naboris.serial_simulator import NaborisSimulator

serial_file_name, serial_directory = "23;53", "2017_May_29"

naboris = Naboris()
plotter = LivePlotter(1)
simulator = NaborisSimulator(naboris, serial_file_name, serial_directory, plotter)

Robot.run(simulator, plotter)
