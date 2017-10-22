import matplotlib

matplotlib.use('Agg')

from atlasbuggy.camera import VideoPlayer, CameraViewer
from atlasbuggy.logparser import LogParser
from atlasbuggy.plotters import StaticPlotter, RobotPlot
from atlasbuggy.subscriptions import *
from atlasbuggy import DataStream
from atlasbuggy import Robot

from naboris import Naboris
from naboris.hough_pipeline import NaborisPipeline
from naboris.naboris_site import NaborisWebsite


class DummyCommandLine(DataStream):
    def __init__(self):
        super(DummyCommandLine, self).__init__(True)

    def handle_input(self, line):
        print(line)


def key_press_fn(event):
    if event.key == "q":
        plotter.exit()

dummy_plot = RobotPlot("dummy")
dummy_plot.update([0, 1, 2], [4, 3, 5])


robot = Robot(log_level=10)

simulator = LogParser("logs/2017_Jun_10/21;25;23.log.xz", enabled=True, update_rate=0.1)
plotter = StaticPlotter(1, dummy_plot, enabled=True)
naboris = Naboris()
capture = VideoPlayer(file_name="videos/naboris/2017_Jun_10/21_25_23.mp4", enabled=True)
viewer = CameraViewer(enabled=False, enable_trackbar=False)
pipeline = NaborisPipeline(enabled=False)
site = NaborisWebsite("templates", "static")
dummy_cmd = DummyCommandLine()

simulator.look_for(naboris)

viewer.subscribe(Update(viewer.capture_tag, pipeline))
pipeline.subscribe(Update(pipeline.capture_tag, capture))
site.subscribe(Update(site.camera_tag, capture))
site.subscribe(Update(site.pipeline_tag, pipeline))
site.subscribe(Subscription(site.cmd_tag, dummy_cmd))
site.subscribe(Subscription(site.plotter_tag, plotter))

plotter.plot()
robot.run(simulator, viewer, site, capture, pipeline)
