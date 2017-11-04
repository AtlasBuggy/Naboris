from atlasbuggy import Orchestrator, run
from atlasbuggy.opencv import OpenCVViewer, OpenCVVideo, OpenCVCamera

from naboris.orbslam2.pipeline import OrbslamPipeline


class BarcodeOrchestrator(Orchestrator):
    def __init__(self, event_loop):
        self.set_default(level=30)
        super(BarcodeOrchestrator, self).__init__(event_loop)

        self.capture = OpenCVVideo(
            # file_name="2017_May_28/16_23_21.mp4",
            # file_name="2017_Jul_31/16_34_21-2.mp4",
            # file_name="2017_Jul_31/16_34_21-3.mp4",
            file_name="2017_Oct_27/NaborisOrchestrator/15_49_00.mp4",
            # file_name="2017_Oct_27/NaborisOrchestrator/15_49_28.mp4",
            # file_name="2017_Oct_27/NaborisOrchestrator/15_50_30.mp4",
            directory="videos/naboris")
        # self.capture = OpenCVCamera(800, 500, capture_number=0)

        self.pipeline = OrbslamPipeline("naboris/orbslam2/ORBvoc.txt", "naboris/orbslam2/naboris.yaml", visualize=True)

        self.add_nodes(self.capture, self.pipeline)

        self.subscribe(self.capture, self.pipeline, self.pipeline.capture_tag)


run(BarcodeOrchestrator)
