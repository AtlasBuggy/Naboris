import time
import cv2
import numpy as np
from atlasbuggy.datastream import DataStream
from atlasbuggy.filestream import BaseFile
from threading import Lock


class CameraStream(DataStream):
    def __init__(self, enabled, debug, threaded, asynchronous, debug_name, logger, recorder):
        self.capture = None

        self.width = None
        self.height = None
        self.fps = None

        self.frame = None
        self.bytes_frame = None
        self.num_frames = 0
        self.frame_lock = Lock()

        self.logger = logger
        self.recorder = recorder

        self.log = logger is not None and logger.enabled
        self.should_record = recorder is not None and recorder.enabled

        self.paused = False
        self.running = False

        super(CameraStream, self).__init__(enabled, debug, threaded, asynchronous, debug_name)

    def log_frame(self):
        if self.log and self.should_record and self.recorder.is_recording:
            self.logger.record(time.time(), self.name, str(self.num_frames))

    def get_frame(self):
        with self.frame_lock:
            return self.frame

    def get_bytes_frame(self):
        with self.frame_lock:
            return self.bytes_frame

    @staticmethod
    def bytes_to_numpy(frame):
        return cv2.imdecode(np.fromstring(frame, dtype=np.uint8), 1)

    @staticmethod
    def numpy_to_bytes(frame):
        return cv2.imencode(".jpg", frame)[1].tostring()


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
