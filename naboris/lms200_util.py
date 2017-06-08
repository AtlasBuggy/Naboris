import time

from atlasbuggy.robot import Robot
from atlasbuggy.ui.plotters.liveplotter import LivePlotter
from atlasbuggy.ui.plotters.plot import RobotPlot
from naboris.lms200 import LMS200

is_live = False


class MyLMS(LMS200):
    def __init__(self):
        super(MyLMS, self).__init__("/dev/cu.usbserial", is_live=is_live)

    def point_cloud_received(self, point_cloud):
        scan_plot.update(point_cloud[:, 0], point_cloud[:, 1])
        time.sleep(0.1)


scan_plot = RobotPlot("lms200", marker='.', linestyle='')
plotter = LivePlotter(1, scan_plot)
lms200 = MyLMS()


def start(robot):
    if not is_live:
        with open("buffer1.txt", 'rb') as buffer_file:
            contents = buffer_file.read()
        lms200.append_simulated_data(contents)


Robot.run(lms200, plotter, setup_fn=start)
