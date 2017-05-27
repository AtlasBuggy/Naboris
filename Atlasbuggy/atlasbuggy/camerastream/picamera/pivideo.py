from atlasbuggy.filestream import BaseFile


class PiVideoRecorder(BaseFile):
    def __init__(self, file_name, directory, capture, recorder_options):
        super(PiVideoRecorder, self).__init__(file_name, directory, ['mp4', 'avi'], "videos", False, False,
                                              False, False, False)
        self.capture = capture
        self.options = recorder_options

    def start(self):
        self.capture.start_recording(**self.options)

    def close(self):
        self.capture.stop_recording()
