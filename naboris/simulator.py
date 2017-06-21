import asyncio

from atlasbuggy.cameras.cvcamera.cvcameraviewer import CameraViewerWithTrackbar
from atlasbuggy.cameras.videoplayer import VideoPlayer
from atlasbuggy.logparser import LogParser
from atlasbuggy.plotters.liveplotter import LivePlotter
from atlasbuggy.robot import Robot
from naboris import Naboris
from naboris.pipeline import NaborisPipeline


class Simulator(LogParser):
    def __init__(self, file_name, directory, enabled=True, log_level=None):
        super(Simulator, self).__init__(file_name, directory, enabled, log_level=log_level)
        self.naboris = None

    def take(self):
        self.naboris = self.streams["naboris"]

    async def update(self):
        await asyncio.sleep(0.01)


class MyCameraViewer(CameraViewerWithTrackbar):
    def __init__(self):
        super(MyCameraViewer, self).__init__()
        self.pipeline = None

    def take(self):
        self.take_video_player()
        self.pipeline = self.streams["pipeline"]

    def get_frame(self):
        self.update_slider_pos()
        return self.pipeline.frame


def key_press_fn(event):
    if event.key == "q":
        plotter.exit()


robot = Robot()

simulator = Simulator("21;25;23.log.xz", "logs/2017_Jun_10")
naboris = Naboris(plot=True)
plotter = LivePlotter(1, enabled=naboris.should_plot, matplotlib_events=dict(key_press_event=key_press_fn),
                      close_when_finished=True)
capture = VideoPlayer("21_25_23.mp4", "videos/naboris/2017_Jun_10")
viewer = MyCameraViewer()
pipeline = NaborisPipeline()

simulator.give(naboris=naboris)
naboris.give(plotter=plotter)
viewer.give(video_player=capture, pipeline=pipeline)
pipeline.give(capture=capture)

robot.run(simulator, plotter, viewer, capture, pipeline)
