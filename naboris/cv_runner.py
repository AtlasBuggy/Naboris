from atlasbuggy import Robot
from atlasbuggy.camera.video.videoplayer import VideoPlayer
from atlasbuggy.camera.viewer.viewer import CameraViewer
from atlasbuggy.subscriptions import Update
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


robot = Robot(log_level=10)

capture = VideoPlayer(file_name="videos/naboris/2017_Jul_14/22_36_21-8.mp4", loop_video=True)
viewer = MyCameraViewer()
pipeline = NaborisPipeline()

viewer.subscribe(Update(viewer.capture_tag, capture))
viewer.subscribe(Update(viewer.pipeline_tag, pipeline))
pipeline.subscribe(Update(pipeline.capture_tag, capture))

robot.run(viewer, capture, pipeline)
