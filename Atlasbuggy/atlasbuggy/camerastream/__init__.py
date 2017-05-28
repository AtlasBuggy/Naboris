from atlasbuggy.datastream import DataStream


class CameraStream(DataStream):
    def __init__(self, enabled, debug, threaded, asynchronous, debug_name=None, logger=None):
        self.width = None
        self.height = None
        self.fps = None
        self.frame = None
        self.running = False
        self.num_frames = 0
        self.logger = logger
        self.capture = None
        self.paused = False
        self.is_recording = False

        super(CameraStream, self).__init__(enabled, debug, threaded, asynchronous, debug_name)
