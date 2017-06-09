import time
from atlasbuggy.ui.plotters.plot import RobotPlot
from atlasbuggy.ui.plotters.liveplotter import LivePlotter
from lms200 import LMS200

scan_plot = RobotPlot("lms200", marker='.', linestyle='')
plotter = LivePlotter(1, scan_plot)


class MyLMS(LMS200):
    def __init__(self, is_live, logger=None):
        super(MyLMS, self).__init__("/dev/cu.usbserial", is_live=is_live, logger=logger)

    def point_cloud_received(self, point_cloud):
        scan_plot.update(point_cloud[:, 0], point_cloud[:, 1])
