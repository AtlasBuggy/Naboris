import numpy as np
import logging
from atlasbuggy.plotters.plot import RobotPlot
from atlasbuggy.plotters.liveplotter import LivePlotter
from sicklms.lms import SickLMS
from sicklms.constants import *


class MyLMS(SickLMS):
    def __init__(self, enabled=True):
        self.scan_plot = RobotPlot("lms200", marker='.', linestyle='')
        self.plotter = LivePlotter(1, self.scan_plot, enabled=True, exit_all=True, default_resize_behavior=False)

        super(MyLMS, self).__init__("/dev/cu.usbserial", enabled=enabled, log_level=logging.INFO, dude_bro_mode=False)

    def start_up_commands(self):
        self.set_range(8)

    def point_cloud_received(self, point_cloud):
        self.scan_plot.update(point_cloud[:, 0], point_cloud[:, 1])
        print(self.update_rate)
        # print("max distance:", np.max(self.distances))
