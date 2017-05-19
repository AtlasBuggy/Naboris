import time
import io
import picamera
from atlasbuggy.datastream import DataStream


class PiCamera(DataStream):
    def __init__(self, name, enabled=True):
        super(PiCamera, self).__init__(name, enabled, False, True, False)
        self.paused = False
        self.camera = None
        self.frame = None
        self.last_access = 0.0

    def get_frame(self):
        self.last_access = time.time()
        self.paused = False
        return self.frame

    def init_camera(self, camera):
        pass

    def run(self):
        with picamera.PiCamera() as camera:
            self.camera = camera
            self.init_camera(self.camera)

            # let camera warm up
            camera.start_preview()
            time.sleep(2)

            stream = io.BytesIO()
            for _ in camera.capture_continuous(stream, 'jpeg', use_video_port=True):
                # store frame
                stream.seek(0)
                self.frame = stream.read()

                # reset stream for next frame
                stream.seek(0)
                stream.truncate()

                # if there hasn't been any clients asking for frames in
                # the last 10 seconds stop the thread
                if time.time() - self.last_access > 10:
                    self.paused = True

                while self.paused:
                    time.sleep(0.1)
