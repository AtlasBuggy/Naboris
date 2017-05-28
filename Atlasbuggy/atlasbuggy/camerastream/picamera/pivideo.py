from atlasbuggy.filestream import BaseFile, default_video_name, default_log_dir_name


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
            self.capture.stop_recording()
            self.recording = False
