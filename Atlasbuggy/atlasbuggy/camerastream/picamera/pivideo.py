import os
import time
from subprocess import Popen, PIPE, DEVNULL
from atlasbuggy.filestream import BaseFile, default_video_name, default_log_dir_name


class H264toMP4converter:
    # expects that MP4Box be installed
    def __init__(self, full_path):
        self.full_path = full_path

        ext_index = self.full_path.rfind(".")
        self.new_path = self.full_path[:ext_index]

        self.process = None
        self.output = None

    def start(self):
        print("Converting video to mp4: '%s'" % self.new_path)
        if os.path.isfile(self.new_path):
            os.remove(self.new_path)
        self.process = Popen(['MP4Box', '-add', self.full_path, self.new_path], stdin=PIPE,
                             stdout=DEVNULL, close_fds=True, bufsize=0)
        self.output = None

        assert self.process is not None

    def is_running(self):
        if self.process is not None:
            time.sleep(0.001)
            self.output = self.process.poll()

        return self.output is None


class PiVideoRecorder(BaseFile):
    def __init__(self, file_name, directory, capture, recorder_options):
        file_name, directory = self.format_path_as_time(
            file_name, directory, default_video_name, default_log_dir_name
        )

        super(PiVideoRecorder, self).__init__(file_name, directory, 'h264', "videos", False, False,
                                              False, False, False)
        self.capture = capture
        self.options = recorder_options
        self.make_dir()
        self.recording = False

    def start(self):
        if not self.recording:
            print("Recording video on '%s'" % self.full_path)
            self.capture.start_recording(self.full_path, 'h264', **self.options)
            self.recording = True

    def close(self):
        if self.recording:
            # self.capture.stop_recording()
            self.recording = False

            converter = H264toMP4converter(self.full_path)
            converter.start()
            while converter.is_running():  pass

            os.remove(self.full_path)
