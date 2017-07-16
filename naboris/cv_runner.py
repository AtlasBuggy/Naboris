from atlasbuggy import Robot
from atlasbuggy.camera.video.videoplayer import VideoPlayer
from atlasbuggy.camera.viewer.viewer import CameraViewer
from atlasbuggy.subscriptions import *
from atlasbuggy.plotters import LivePlotter, RobotPlot, RobotPlotCollection
import asyncio

from naboris.pipeline import NaborisPipeline


class MyCameraViewer(CameraViewer):
    def __init__(self):
        super(MyCameraViewer, self).__init__(enabled=True)

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


class RhoThetaPlotter(LivePlotter):
    def __init__(self, enabled=True):
        self.rho_theta_plot_1 = RobotPlot("rho_theta_1", marker=".", linestyle='', color='red')
        self.rho_theta_plot_2 = RobotPlot("rho_theta_2", marker=".", linestyle='', color='blue')
        self.cluster_plot_centers = RobotPlot("centers", marker="s", linestyle='', color='green')
        plot_collection = RobotPlotCollection("rho_theta", self.rho_theta_plot_1, self.rho_theta_plot_2,
                                              self.cluster_plot_centers)

        super(RhoThetaPlotter, self).__init__(1, plot_collection, default_resize_behavior=False, enabled=enabled)

        self.pipeline_tag = "pipeline"
        self.results_service_tag = "results"
        self.pipeline_feed = None
        self.require_subscription(self.pipeline_tag, Feed, service=self.results_service_tag)

    def take(self, subscriptions):
        self.pipeline_feed = subscriptions[self.pipeline_tag].get_feed()

    async def update(self):
        while not self.pipeline_feed.empty():
            cluster1, cluster2, center = await self.pipeline_feed.get()
            self.pipeline_feed.task_done()

            self.rho_theta_plot_1.extend(cluster1[:, 0], cluster1[:, 1])
            self.rho_theta_plot_2.extend(cluster2[:, 0], cluster2[:, 1])
            self.cluster_plot_centers.extend(center[:, 0], center[:, 1])
        await asyncio.sleep(0.001)


robot = Robot(log_level=10)

video_name = "videos/naboris/2017_Jul_14/22_36_21-7.mp4"
# video_name = "videos/naboris/2017_Jul_14/23_24_32-2.mp4"
capture = VideoPlayer(file_name=video_name, loop_video=True)
viewer = MyCameraViewer()
pipeline = NaborisPipeline()
# plotter = RhoThetaPlotter(enabled=False)

viewer.subscribe(Update(viewer.capture_tag, capture))
viewer.subscribe(Update(viewer.pipeline_tag, pipeline))
pipeline.subscribe(Update(pipeline.capture_tag, capture))
# plotter.subscribe(Feed(plotter.pipeline_tag, pipeline, plotter.results_service_tag))

robot.run(viewer, capture, pipeline)
