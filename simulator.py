import matplotlib
import webbrowser

matplotlib.use('Agg')

from atlasbuggy.camera import VideoPlayer, CameraViewer
from atlasbuggy.logparser import LogParser
from atlasbuggy.plotters import LivePlotter
from atlasbuggy.subscriptions import *
from atlasbuggy import DataStream
from atlasbuggy import Robot

from naboris import Naboris
from naboris.hough_pipeline import NaborisPipeline
from naboris.site import NaborisWebsite


class DummyCommandLine(DataStream):
    def __init__(self):
        super(DummyCommandLine, self).__init__(True)

    def handle_input(self, line):
        print(line)


def key_press_fn(event):
    if event.key == "q":
        plotter.exit()


robot = Robot(log_level=10)

simulator = LogParser("logs/2017_Jun_10/21;25;23.log.xz", enabled=True, update_rate=0.001)
plotter = LivePlotter(1, matplotlib_events=dict(key_press_event=key_press_fn),
                      close_when_finished=True, enabled=True)
naboris = Naboris()
capture = VideoPlayer(file_name="videos/naboris/2017_Jun_10/21_25_23.mp4", enabled=True)
viewer = CameraViewer(enabled=True, enable_trackbar=True)
pipeline = NaborisPipeline(enabled=True)
site = NaborisWebsite("templates", "static", enabled=True)
dummy_cmd = DummyCommandLine()

viewer.subscribe(Update(viewer.capture_tag, pipeline))
pipeline.subscribe(Update(pipeline.capture_tag, capture))
naboris.subscribe(Subscription(naboris.plotter_tag, plotter))

site.subscribe(Update(site.camera_tag, capture))
site.subscribe(Update(site.pipeline_tag, pipeline))
site.subscribe(Subscription(site.cmd_tag, dummy_cmd))
site.subscribe(Subscription(site.plotter_tag, plotter))

simulator.subscribe(Subscription("naboris", naboris))

webbrowser.open("0.0.0.0:5000")

robot.run(simulator, plotter, viewer, site, capture, pipeline)
