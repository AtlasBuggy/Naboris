import os
import time
import asyncio
from threading import Thread, Event
from subprocess import Popen, PIPE, DEVNULL

import picamera
from picamera.array import PiRGBArray

from atlasbuggy import Node
from atlasbuggy.opencv.messages import ImageMessage


class PiCamera(Node):
    def __init__(self, enabled=True, record=False, file_name=None, directory=None):
        super(PiCamera, self).__init__(enabled)

        self.width = 0
        self.height = 0
        self.fps = 32
        self.capture = None

        self.default_file_type = ".h264"
        self.default_length = len(self.default_file_type)

        self.should_record = record
        self.is_recording = False
        self.file_name = file_name
        self.directory = directory
        self.full_path = ""

        self.length_sec = 0.0

        self.fps_sum = 0.0
        self.fps_avg = 30.0
        self.prev_t = None

        self.frame = None
        self.num_frames = 0

        self.paused = False
        self.camera_thread = Thread(target=self.run)
        self.exit_event = Event()

    async def setup(self):
        self.logger.debug("PiCamera setup")
        self.capture = picamera.PiCamera()

        # self.capture.resolution = (self.capture.resolution[0] // 2, self.capture.resolution[1] // 2)
        self.capture.framerate = self.fps
        self.capture.hflip = True
        self.capture.vflip = True

        self.width = self.capture.resolution[0]
        self.height = self.capture.resolution[1]

        self.logger.info("PiCamera initialized: %s" % self.capture)

        self.camera_thread.start()

    def start_recording(self, file_name=None, directory=None):
        self.set_path(file_name, directory)
        self.num_frames = 0
        self.make_dirs()
        self.logger.info("Recording video on '%s'" % self.full_path)
        self.capture.start_recording(self.full_path)
        self.is_recording = True

    def set_pause(self, state):
        self.paused = state

    def get_pause(self):
        return self.paused

    def current_frame_num(self):
        return self.num_frames

    def make_dirs(self):
        if self.directory is not None and len(self.directory) > 0 and not os.path.isdir(self.directory):
            os.makedirs(self.directory)

    def set_path(self, file_name=None, directory=None):
        if file_name is None:
            file_name = time.strftime("%H_%M_%S.mp4")
            if directory is None:
                # only use default if both directory and file_name are None.
                # Assume file_name has the full path if directory is None
                directory = time.strftime("videos/%Y_%b_%d")

        self.file_name = file_name
        self.directory = directory

        if not self.file_name.endswith(self.default_file_type):
            self.file_name += self.default_file_type

        self.full_path = os.path.join(self.directory, self.file_name)

    async def loop(self):
        while True:
            if self.frame is not None and not self.paused:
                message = ImageMessage(self.frame, self.num_frames)
                self.log_to_buffer(time.time(), "PiCamera image received: %s" % message)
                num_broadcasts = await self.broadcast(message)
                self.frame = None
            else:
                await asyncio.sleep(1 / self.fps)

    def run(self):
        with self.capture:
            while not self.exit_event.is_set():
                self.logger.info("Warming up camera")
                self.capture.start_preview()
                time.sleep(2)

                if self.should_record:
                    self.start_recording(self.file_name, self.directory)

                raw_capture = PiRGBArray(self.capture, size=self.capture.resolution)
                for frame in self.capture.capture_continuous(raw_capture, format="bgr", use_video_port=True):

                    self.frame = frame.array
                    raw_capture.truncate(0)

                    self.poll_for_fps()
                    if self.exit_event.is_set():
                        return

                    if self.paused:
                        time.sleep(0.1)
                        continue

    def poll_for_fps(self):
        if self.prev_t is None:
            self.prev_t = time.time()
            return 0.0

        self.length_sec = time.time() - self.start_time
        self.fps_sum += 1 / (time.time() - self.prev_t)
        self.num_frames += 1
        self.fps_avg = self.fps_sum / self.num_frames
        self.prev_t = time.time()

    def stop_recording(self):
        if self.enabled and self.is_recording:
            self.capture.stop_recording()
            self.is_recording = False

            if self.file_name.endswith(self.default_file_type):
                self.file_name = self.file_name[:-self.default_length]

            if self.file_name.endswith(".mp4"):
                converter = H264toMP4converter(self.full_path)
                converter.start()

                while converter.is_running():
                    for line in converter.process.stderr:
                        self.logger.debug(line.strip())

                if not os.path.isfile(converter.new_path):
                    raise RuntimeError("Failed to create MP4 file for some reason!!")
                self.logger.debug("Conversion complete! Removing temp file: '%s'" % self.full_path)
                os.remove(self.full_path)
            else:
                self.logger.debug("Skipping conversion to mp4")

            self.logger.info("Wrote video to '%s'" % self.full_path)

    @asyncio.coroutine
    def teardown(self):
        # self.capture.stop_preview()  # picamera complains when this is called while recording
        self.stop_recording()
        self.exit_event.set()


class H264toMP4converter:
    # expects that MP4Box be installed, sudo apt-get install gpac
    def __init__(self, full_path):
        self.full_path = full_path

        ext_index = self.full_path.rfind(".")
        self.new_path = self.full_path[:ext_index]

        self.process = None
        self.output = None

    def start(self):
        # print("Converting video to mp4: '%s'" % self.new_path)
        if os.path.isfile(self.new_path):
            os.remove(self.new_path)
        self.process = Popen("/usr/bin/MP4Box -add %s %s" % (self.full_path, self.new_path),
                             stdout=DEVNULL, stderr=PIPE, bufsize=1, universal_newlines=True, shell=True)
        self.output = None

        assert self.process is not None

    def is_running(self):
        if self.process is not None:
            time.sleep(0.001)
            self.output = self.process.poll()

        return self.output is None
