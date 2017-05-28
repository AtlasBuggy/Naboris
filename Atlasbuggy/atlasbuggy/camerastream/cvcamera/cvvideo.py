import cv2
from atlasbuggy.filestream import BaseFile, default_video_name, default_log_dir_name
from atlasbuggy import get_platform


class CvVideoRecorder(BaseFile):
    def __init__(self, file_name, directory, width, height):
        file_name, directory = self.format_path_as_time(
            file_name, directory, default_video_name, default_log_dir_name
        )

        super(CvVideoRecorder, self).__init__(file_name, directory, ['mp4', 'avi'], "videos", False, True,
                                              False, False, False)
        self.width = width
        self.height = height
        self.video_writer = None
        self.fourcc = None
        self.frame_buffer = []
        self.opened = False

    def start(self):
        if self.file_name.endswith('avi'):
            codec = 'MJPG'
        elif self.file_name.endswith('mp4'):
            if get_platform() == 'mac':
                codec = 'mp4v'
            else:
                # TODO: Figure out mp4 recording in ubuntu
                # codec = 'X264'
                codec = 'MJPG'
                self.file_name = self.file_name[:-3] + "avi"
                self.full_path = self.full_path[:-3] + "avi"
        else:
            raise ValueError("Invalid file format")
        self.fourcc = cv2.VideoWriter_fourcc(*codec)
        self.video_writer = cv2.VideoWriter()

    def _open(self, fps):
        self.video_writer.open(self.full_path, self.fourcc, fps, (self.width, self.height), True)

    def write(self, frame, fps):
        if not self.opened:
            if len(self.frame_buffer) >= 50:
                self._open(fps)
                self.opened = True
                print("Writing video to: '%s'. FPS: %0.2f" % (self.full_path, fps))

                while len(self.frame_buffer) != 0:
                    self._write_frame(frame.pop(0))
            else:
                self.frame_buffer.append(frame)
        else:
            self._write_frame(frame)

    def _write_frame(self, frame):
        if frame.shape[0:2] != (self.height, self.width):
            frame = cv2.resize(frame, (self.height, self.width))
        if len(frame.shape) == 2:
            self.video_writer.write(cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR))
        else:
            self.video_writer.write(frame)

    def close(self):
        self.video_writer.release()
