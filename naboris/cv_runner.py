from atlasbuggy import Robot
from atlasbuggy.camera.video.videoplayer import VideoPlayer
from atlasbuggy.camera.viewer.viewer import CameraViewer
from atlasbuggy.subscriptions import *
from atlasbuggy.plotters import LivePlotter, RobotPlot, RobotPlotCollection
import asyncio

from naboris.pipeline import DepthPipeline


class MyCameraViewer(CameraViewer):
    def __init__(self, enabled=True):
        super(MyCameraViewer, self).__init__(enabled)

        self.pipeline_tag = "pipeline"

        self.pipeline = None
        self.pipeline_feed = None

        self.show_original = False

        self.require_subscription(self.pipeline_tag, Update)

    def take(self, subscriptions):
        self.take_capture(subscriptions)
        self.pipeline = subscriptions[self.pipeline_tag].get_stream()
        self.pipeline_feed = subscriptions[self.pipeline_tag].get_feed()
        self.set_feed()

    def set_feed(self):
        if self.show_original:
            self.pipeline_feed.enabled = False
            self.capture_feed.enabled = True
        else:
            self.pipeline_feed.enabled = True
            self.capture_feed.enabled = False

    def get_frame_from_feed(self):
        if self.show_original:
            return self.capture_feed.get()
        else:
            return self.pipeline_feed.get()

    def key_down(self, key):
        if key == 'o':
            self.show_original = not self.show_original
            self.set_feed()
        elif key == 'q':
            self.exit()
        elif key == ' ':
            self.toggle_pause()
            if self.is_paused():
                self.pipeline_feed.enabled = False
                self.capture_feed.enabled = False
            else:
                self.pipeline_feed.enabled = True
                self.capture_feed.enabled = True


class DataPlotter(LivePlotter):
    def __init__(self, enabled=True):
        self.position_plot = RobotPlot("position_plot", marker=".", linestyle='-', color='red', enabled=False)

        self.top_dist_plot = RobotPlot("top_dist_plot", color="blue")
        self.left_dist_plot = RobotPlot("left_dist_plot", color="green")
        self.right_dist_plot = RobotPlot("right_dist_plot", color="red")
        self.distance_plot = RobotPlotCollection("dist_plot", self.top_dist_plot, self.left_dist_plot, self.right_dist_plot)

        super(DataPlotter, self).__init__(2, self.position_plot, self.distance_plot, active_window_resizing=False,
                                          enabled=enabled)

        self.pipeline_tag = "pipeline"
        self.results_service_tag = "results"
        self.pipeline_feed = None
        self.require_subscription(self.pipeline_tag, Feed, service=self.results_service_tag)

        max_limit = 900
        self.x_limits = [-max_limit, max_limit]
        self.y_limits = [-max_limit, max_limit]

    def start(self):
        self.get_axis(self.distance_plot).set_xlim(self.x_limits)
        self.get_axis(self.distance_plot).set_ylim(self.y_limits)

    def take(self, subscriptions):
        self.pipeline_feed = subscriptions[self.pipeline_tag].get_feed()

    async def update(self):
        while not self.pipeline_feed.empty():
            position, rotation, distances = await self.pipeline_feed.get()
            self.pipeline_feed.task_done()

            self.position_plot.append(position[0], position[1])

            print(distances)
            left_dist, right_dist, top_dist = distances

            if left_dist is not None:
                self.left_dist_plot.update([left_dist, left_dist], self.y_limits)
                self.left_dist_plot.set_properties(color="blue")
            else:
                self.left_dist_plot.set_properties(color="gray")

            if right_dist is not None:
                self.right_dist_plot.update([right_dist, right_dist], self.y_limits)
                self.right_dist_plot.set_properties(color="green")
            else:
                self.right_dist_plot.set_properties(color="gray")
            if top_dist is not None:
                self.top_dist_plot.update(self.x_limits, [top_dist, top_dist])
                self.top_dist_plot.set_properties(color="red")
            else:
                self.top_dist_plot.set_properties(color="gray")

        await asyncio.sleep(0.001)


robot = Robot(log_level=10)

# video_name = "videos/naboris/2017_Jul_14/22_36_21-1.mp4"
video_name = "videos/naboris/2017_Jul_14/23_24_32-3.mp4"
capture = VideoPlayer(file_name=video_name, loop_video=True, enabled=True)
viewer = MyCameraViewer(enabled=True)
pipeline = DepthPipeline("depth_models/coarse", "depth_models/fine", enabled=True)
plotter = DataPlotter(enabled=False)

viewer.subscribe(Update(viewer.capture_tag, capture))
viewer.subscribe(Update(viewer.pipeline_tag, pipeline))
pipeline.subscribe(Update(pipeline.capture_tag, capture))
plotter.subscribe(Feed(plotter.pipeline_tag, pipeline, plotter.results_service_tag))

robot.run(viewer, capture, pipeline, plotter)
