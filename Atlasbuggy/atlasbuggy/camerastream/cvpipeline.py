from atlasbuggy.datastream import DataStream


class CvPipeline(DataStream):
    def __init__(self, capture, enabled, debug, name=None):
        super(CvPipeline, self).__init__(enabled, debug, True, False, name)
        self.capture = capture
        self.frame = None

        self.pipeline.frame = self.camera.get_frame()
        self.pipeline.update()
        frame = self.pipeline.raw_frame()

    def run(self):
        while True:
            self.frame = self.capture.get_frame()
            if self.frame is not None:
                self.pipeline(self.frame)
            self.update()

    def pipeline(self, frame):
        pass
