from atlasbuggy.robot import Robot
from atlasbuggy.ui.plotters.liveplotter import LivePlotter
from naboris import Naboris
from naboris.simulator import NaborisSimulator

serial_file_name, serial_directory = "23;53", "2017_May_29"

naboris = Naboris()
naboris.actuators.enable_led_plot = True
plotter = LivePlotter(1)
simulator = NaborisSimulator(naboris, serial_file_name, serial_directory, plotter)

Robot.run(simulator, plotter)
