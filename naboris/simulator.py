import asyncio

from atlasbuggy.cameras.videoplayer import VideoPlayer
from atlasbuggy.cameras.viewer.trackbar import CameraViewerWithTrackbar
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
        self.take_capture()
        self.pipeline = self.streams["pipeline"]

    def check_feed_for_frames(self):
        frame = None
        output = None
        while not self.check_feed(self.pipeline).empty():
            output = self.check_feed(self.pipeline).get()

        if output is not None:
            if self.pipeline.post_bytes:
                frame, bytes_frame = output
            else:
                frame = output[0]
        return frame


def key_press_fn(event):
    if event.key == "q":
        plotter.exit()


robot = Robot(log_level=10)

simulator = Simulator("16;23;21.log.xz", "logs/2017_May_28", False)
naboris = Naboris(plot=False)
plotter = LivePlotter(1, enabled=naboris.should_plot, matplotlib_events=dict(key_press_event=key_press_fn),
                      close_when_finished=True)
capture = VideoPlayer("16_23_21.mp4", "videos/naboris/2017_May_28")
viewer = MyCameraViewer()
pipeline = NaborisPipeline()

simulator.give(naboris=naboris)
naboris.give(plotter=plotter)
viewer.give(capture=capture, pipeline=pipeline)
pipeline.give(capture=capture)

viewer.subscribe(pipeline=pipeline)
pipeline.subscribe(capture=capture)

robot.run(simulator, plotter, viewer, capture, pipeline)
