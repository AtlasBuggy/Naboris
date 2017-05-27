import cv2
import time
from atlasbuggy.camerastream import CameraStream
from atlasbuggy.filestream import BaseFile

default_video_name = "%H_%M_%S"
default_video_dir = "%Y_%b_%d"


class VideoPlayer(CameraStream):
    def __init__(self, file_name, directory, width=None, height=None, enabled=True, debug=False, frame_skip=0,
                 loop_video=False, start_frame=0):
        file_name, directory = BaseFile.format_path_as_time(
            file_name, directory, default_video_name, default_video_dir
        )

        self.file_info = BaseFile(file_name, directory, ['mp4', 'avi'], "videos", False, True, False, False, False)

        super(VideoPlayer, self).__init__(enabled, debug, True, False, self.file_info.file_name)

        cv2.namedWindow(self.name)
        self.capture = cv2.VideoCapture(self.file_info.full_path)

        self.fps = self.capture.get(cv2.CAP_PROP_FPS)
        self.num_frames = int(self.capture.get(cv2.CAP_PROP_FRAME_COUNT))
        if self.num_frames <= 0:
            raise FileNotFoundError("Video failed to load... No frames found!")

        self.length_sec = self.num_frames / self.fps

        self.width = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.resize_frame = False

        self.slider_ticks = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH) // 3)
        if self.slider_ticks > self.num_frames:
            self.slider_ticks = self.num_frames
        self.slider_name = None

        if width is None:
            self.resize_width = self.width
        else:
            self.resize_width = width
            self.resize_frame = True

        if height is None:
            self.resize_height = self.height
        else:
            self.resize_height = height
            self.resize_frame = True

        self.current_frame = 0
        self.next_frame = 1

        self.frame_skip = frame_skip
        self.loop_video = loop_video

        if start_frame > 0:
            self.set_frame(start_frame)

    def link_slider(self, slider_name):
        self.slider_name = slider_name

    def current_pos(self):
        return int(self.capture.get(cv2.CAP_PROP_POS_FRAMES))

    def current_time(self):
        return self.current_pos() * self.length_sec / self.num_frames

    def set_frame(self, position):
        self.next_frame = position

    def _set_frame(self, position):
        if position >= self.num_frames:
            position = self.num_frames
        if position >= 0:
            self.capture.set(cv2.CAP_PROP_POS_FRAMES, int(position))

    def get_frame(self):
        if self.frame_skip > 0:
            self._set_frame(self.current_pos() + self.frame_skip)

        if self.next_frame - self.current_frame != 1:
            self._set_frame(self.next_frame)

        self.current_frame = self.next_frame
        self.next_frame += 1

        success, self.frame = self.capture.read()

        if self.slider_name is not None:
            slider_pos = int(self.current_frame * self.slider_ticks / self.num_frames)
            cv2.setTrackbarPos(self.slider_name, self.name, slider_pos)

        if not success or self.frame is None:
            if self.loop_video:
                self.set_frame(0)
                while success is False or self.frame is None:
                    success, self.frame = self.capture.read()
            else:
                self.exit()
                return
        if self.resize_frame:
            self.frame = cv2.resize(self.frame,
                                    (self.resize_width, self.resize_height),
                                    interpolation=cv2.INTER_NEAREST)

    def run(self):
        while self.are_others_running():
            self.get_frame()
            self.update()
            time.sleep(1 / self.fps)
