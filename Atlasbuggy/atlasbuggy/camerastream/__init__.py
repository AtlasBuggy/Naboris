import time
from atlasbuggy.datastream import DataStream
from atlasbuggy.filestream import BaseFile


class CameraStream(DataStream):
    def __init__(self, enabled, debug, threaded, asynchronous, debug_name, logger, recorder):
        self.capture = None

        self.width = None
        self.height = None
        self.fps = None

        self.frame = None
        self.num_frames = 0

        self.logger = logger
        self.recorder = recorder

        self.log = logger is not None and logger.enabled
        self.should_record = recorder is not None and recorder.enabled

        self.paused = False
        self.running = False

        self.has_updated = False

        super(CameraStream, self).__init__(enabled, debug, threaded, asynchronous, debug_name)

    def log_frame(self):
        if self.log and self.should_record and self.recorder.is_recording:
            self.logger.record(time.time(), self.name, str(self.num_frames))

    def did_update(self):
        if self.has_updated:
            self.has_updated = False
            return True
        else:
            return False


class VideoStream(BaseFile):
    def __init__(self, file_name, directory, file_format, enabled, debug):
        super(VideoStream, self).__init__(
            file_name, directory, file_format, "videos", False, enabled, debug, False, False
        )

        self.capture = None
        self.is_recording = False

    def start_recording(self, capture):
        pass

    def record(self, frame):
        pass

    def stop_recording(self):
        pass
