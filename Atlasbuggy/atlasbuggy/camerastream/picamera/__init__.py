import time
import io
import picamera
import numpy as np
from atlasbuggy.camerastream import CameraStream
from atlasbuggy.camerastream.picamera.pivideo import PiVideoRecorder


class PiCamera(CameraStream):
    def __init__(self, enabled=True, name=None):
        super(PiCamera, self).__init__(enabled, False, True, False, name)
        self.capture = picamera.PiCamera()
        self.init_cam(self.capture)

        self.width = self.capture.width
        self.height = self.capture.height
        self.fps = self.capture.framerate

        self.raw_frame = None
        self.recorder = None

    def init_cam(self, camera):
        pass

    def start_recording(self, file_name=None, directory=None, **options):
        if self.running:
            self.recorder = PiVideoRecorder(file_name, directory, self.capture, options)
            self.recorder.start()
        else:
            raise FileNotFoundError("Camera hasn't started running yet!")

    def stop_recording(self):
        if self.recorder is not None:
            self.recorder.close()

    def update(self):
        pass

    def run(self):
        with self.capture:
            # let self.cam warm up
            self.capture.start_preview()
            time.sleep(2)

            self.running = True

            stream = io.BytesIO()
            for _ in self.capture.capture_continuous(stream, 'jpeg', use_video_port=True):
                # store frame
                stream.seek(0)
                self.raw_frame = stream.read()
                self.frame = np.frombuffer(
                    stream, dtype=np.uint8, count=self.width * self.height
                ).reshape(self.height, self.width)

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
                    self.close()

    def close(self):
        self.stop_recording()
        self.capture.stop_preview()