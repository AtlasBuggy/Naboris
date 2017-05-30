import io
import cv2
import time
import picamera
import numpy as np
from picamera.array import PiRGBArray, bytes_to_rgb
from atlasbuggy.camerastream import CameraStream
from atlasbuggy.camerastream.picamera.pivideo import PiVideoRecorder


class PiCamera(CameraStream):
    def __init__(self, enabled=True, name=None, logger=None, video_recorder=None):
        super(PiCamera, self).__init__(enabled, False, True, False, name, logger, video_recorder)

        self.capture = picamera.PiCamera()
        self.width = self.capture.resolution[0]
        self.height = self.capture.resolution[1]
        self.fps = self.capture.framerate

        self.init_cam(self.capture)

    def init_cam(self, camera):
        pass

    def run(self):
        with self.capture:
            # let camera warm up
            self.capture.start_preview()
            time.sleep(2)

            self.recorder.start_recording(self.capture)
            self.running = True

            # stream = io.BytesIO()
            # for _ in self.capture.capture_continuous(stream, 'jpeg', use_video_port=True):
            #     with self.frame_lock:
            #         # store frame
            #         stream.seek(0)
            #         self.bytes_frame = stream.read()
            #
            #         # reset stream for next frame
            #         stream.seek(0)
            #         stream.truncate()
            #
            #         # self.frame = bytes_to_rgb(self.bytes_frame, self.capture.resolution)
            #         self.frame = np.frombuffer(self.bytes_frame, dtype=np.uint8).reshape((self.height, self.width, 3))[:self.height, :self.width, :]

            raw_capture = PiRGBArray(self.capture, size=self.capture.resolution)
            for frame in self.capture.capture_continuous(raw_capture, format="bgr", use_video_port=True):
                with self.frame_lock:
                    self.frame = frame.array
                    raw_capture.truncate(0)

                    self.log_frame()
                    self.num_frames += 1

                while self.paused:
                    time.sleep(0.1)

                if not self.all_running():
                    return

    def get_bytes_frame(self):
        with self.frame_lock:
            self.bytes_frame = self.numpy_to_bytes(self.frame)
        return self.bytes_frame

    def close(self):
        # self.capture.stop_preview()  # picamera complains when this is called while recording
        self.recorder.stop_recording()
