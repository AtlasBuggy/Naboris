import io
import cv2
import time
import picamera
import numpy as np
from atlasbuggy.camerastream import CameraStream
from atlasbuggy.camerastream.picamera.pivideo import PiVideoRecorder


class PiCamera(CameraStream):
    def __init__(self, enabled=True, name=None, logger=None):
        super(PiCamera, self).__init__(enabled, False, True, False, name, logger)
        self.capture = picamera.PiCamera()
        self.init_cam(self.capture)

        self.width = self.capture.resolution[0]
        self.height = self.capture.resolution[1]
        self.fps = self.capture.framerate

        self.raw_frame = None
        self.recorder = None
        self.is_recording = False

    def init_cam(self, camera):
        pass

    def start_recording(self, file_name=None, directory=None, **options):
        self.is_recording = True
        if file_name is None:
            file_name = self.logger.input_name.replace(";", "_") + ".mp4"
        if directory is None:
            directory = self.logger.input_dir

        self.recorder = PiVideoRecorder(file_name, directory, self.capture, options)

    def stop_recording(self):
        if self.is_recording:
            self.recorder.close()

    def update(self):
        pass

    def run(self):
        with self.capture:
            # let camera warm up
            self.capture.start_preview()
            time.sleep(2)

            self.running = True

            if self.is_recording:
                self.recorder.start()

            stream = io.BytesIO()
            for _ in self.capture.capture_continuous(stream, 'jpeg', use_video_port=True):
                # store frame
                stream.seek(0)
                self.raw_frame = stream.read()
                # self.frame = np.frombuffer(
                #     self.raw_frame, dtype=np.uint8, count=len(self.raw_frame)
                # ).reshape(self.height, self.width)
                # self.frame = cv2.imdecode(np.fromstring(self.raw_frame, dtype=np.uint8), 1)

                if self.is_recording and self.logger is not None:
                    self.logger.record(time.time(), self.name, str(self.num_frames))

                self.num_frames += 1

                # reset stream for next frame
                stream.seek(0)
                stream.truncate()

                self.update()

                # if there hasn't been any clients asking for frames in
                # the last 10 seconds stop the thread

                while self.paused:
                    time.sleep(0.1)

                if not self.are_others_running():
                    return

    def close(self):
        # self.capture.stop_preview()  # picamera complains when this is called while recording
        self.stop_recording()
