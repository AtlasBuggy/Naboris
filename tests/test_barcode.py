import numpy as np

from atlasbuggy import Orchestrator, run
from atlasbuggy.opencv import OpenCVViewer, OpenCVVideo, OpenCVCamera

from naboris.barcode_pipeline import BarcodePipeline


class BarcodeOrchestrator(Orchestrator):
    def __init__(self, event_loop):
        self.set_default(level=30)
        super(BarcodeOrchestrator, self).__init__(event_loop)

        # self.capture = OpenCVVideo(file_name="../qr_demo.avi")
        self.capture = OpenCVCamera(800, 500, capture_number=0)
        self.viewer = OpenCVViewer()

        picam_M = np.array([[743.28794629, 0, 239.16868139], [0, 742.27098752, 216.06257926], [0, 0, 1]])
        distort_k = np.array([-0.01037819, 0.23203598, -0.03144583, -0.04554396, -0.34115987])
        data = b'something'
        # size = np.array([[0, 0], [52, 0], [] [52, 52]])  # mm
        length = 0.15142
        size = np.array([
             [0.0, 0.0, 0.0],
             [0.0, 0.0, length],
             [length, 0.0, 0.0],
             [length, 0.0, length]
        ], dtype=np.double)
        self.pipeline = BarcodePipeline(picam_M, distort_k, data, size)

        self.add_nodes(self.capture, self.viewer, self.pipeline)

        self.subscribe(self.pipeline, self.viewer, self.viewer.capture_tag)
        self.subscribe(self.capture, self.pipeline, self.pipeline.capture_tag)


run(BarcodeOrchestrator)
