import time
import io
import picamera
from atlasbuggy.datastream import DataStream


class PiCamera(DataStream):
    def __init__(self, enabled=True, name=None):
        super(PiCamera, self).__init__(enabled, False, True, False, name)
        self.paused = False

        self.cam = picamera.PiCamera()
        self.init_cam(self.cam)

        self.frame = None
        self.last_access = 0.0

    def get_frame(self):
        self.last_access = time.time()
        return self.frame

    def init_cam(self, camera):
        pass

    def run(self):
        with self.cam:
            # let self.cam warm up
            self.cam.start_preview()
            time.sleep(2)

            stream = io.BytesIO()
            for _ in self.cam.capture_continuous(stream, 'jpeg', use_video_port=True):
                # store frame
                stream.seek(0)
                self.frame = stream.read()

                # reset stream for next frame
                stream.seek(0)
                stream.truncate()

                # if there hasn't been any clients asking for frames in
                # the last 10 seconds stop the thread
                
                while self.paused:
                    time.sleep(0.1)
