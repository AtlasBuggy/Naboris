import logging
from atlasbuggy.plotters.plot import RobotPlot
from atlasbuggy.plotters.liveplotter import LivePlotter
from lms200 import LMS200



class MyLMS(LMS200):
    def __init__(self, is_live, enabled=True):
        self.scan_plot = RobotPlot("lms200", marker='.', linestyle='')
        self.plotter = LivePlotter(1, self.scan_plot)

        super(MyLMS, self).__init__("/dev/cu.usbserial", enabled=enabled, is_live=is_live, log_level=logging.INFO)

    def point_cloud_received(self, point_cloud):
        self.scan_plot.update(point_cloud[:, 0], point_cloud[:, 1])
