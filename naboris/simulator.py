from atlasbuggy.camera import VideoPlayer, CameraViewer
from atlasbuggy.logparser import LogParser
from atlasbuggy.plotters import LivePlotter
from atlasbuggy.subscriptions import *
from atlasbuggy import Robot

from naboris import Naboris
from naboris.pipeline import NaborisPipeline


def key_press_fn(event):
    if event.key == "q":
        plotter.exit()


robot = Robot(log_level=10)

simulator = LogParser("logs/2017_Jun_10/21;25;23.log.xz", enabled=True, update_rate=0.001)
plotter = LivePlotter(1, matplotlib_events=dict(key_press_event=key_press_fn),
                      close_when_finished=True, enabled=True)
naboris = Naboris(plotter=plotter)
capture = VideoPlayer(file_name="videos/naboris/2017_Jun_10/21_25_23.mp4", enabled=False)
viewer = CameraViewer(enabled=False, enable_trackbar=False)
pipeline = NaborisPipeline(enabled=False)

simulator.look_for(naboris)

viewer.subscribe(Update(viewer.capture_tag, pipeline))
pipeline.subscribe(Update(pipeline.capture_tag, capture))

robot.run(simulator, plotter, viewer, capture, pipeline)
