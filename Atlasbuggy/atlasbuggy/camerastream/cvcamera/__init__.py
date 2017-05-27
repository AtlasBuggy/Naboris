import os
import cv2
import time
from atlasbuggy import get_platform
from atlasbuggy.camerastream import CameraStream
from atlasbuggy.camerastream.cvcamera.cvvideo import CvVideoRecorder


class CvCamera(CameraStream):
    captures = {}
    used_captures = set()
    min_cap_num = 0
    max_cap_num = None

    def __init__(self, width=None, height=None, capture_number=None,
                 enabled=True, debug=False, name=None, skip_count=0):
        super(CvCamera, self).__init__(enabled, debug, True, False, name)

        self.capture_number = capture_number

        self.recorder = None
        self.is_recording = False

        self.width = width
        self.height = height
        self.resize_frame = False

        self.skip_count = skip_count

        self.length_sec = 0.0
        self.fps = 30.0
        self.fps_sum = 0.0
        self.fps_avg = 0.0
        self.prev_t = None

        self.key = -1
        platform = get_platform()
        if platform == "linux":
            self.key_codes = {
                65362: "up",
                65364: "down",
                65361: "left",
                65363: "right",
            }
        elif platform == "mac":
            self.key_codes = {
                63232: "up",
                63233: "down",
                63234: "left",
                63235: "right",
            }
        else:
            self.key_codes = {}

    def update_key_codes(self, **new_key_codes):
        self.key_codes.update(new_key_codes)

    def launch_camera(self):
        if not self.enabled:
            return None

        if self.capture_number is None:
            capture, height, width = self.launch_selector()
            if type(capture) == str:
                raise FileNotFoundError(capture)
            if capture is None:
                return "exit"
            self.capture = capture
        else:
            self.capture = self.load_capture(self.capture_number)
            success, frame = self.capture.read()
            if not success:
                raise FileNotFoundError("Camera %s failed to load!" % self.capture_number)
            height, width = frame.shape[0:2]

        if self.height is not None:
            if height != self.height:
                self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                self.resize_frame = True
        else:
            self.height = height

        if self.width is not None:
            if width != self.width:
                self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                self.resize_frame = True
        else:
            self.width = width

    def launch_selector(self):
        selector_window_name = "Select camera for: " + self.name
        selected_capture = None
        current_capture = None
        current_num = 0
        width = None
        height = None

        while current_num in CvCamera.used_captures:
            current_num += 1

            if CvCamera.max_cap_num is not None and current_num > CvCamera.max_cap_num:
                return "No cameras left!", height, width

            try:
                current_capture = self.load_capture(current_num)
                success, frame = current_capture.read()
                if not success:
                    raise cv2.error
            except cv2.error:
                CvCamera.max_cap_num = current_num - 1
                current_capture.release()
                return "No cameras left!", height, width

        current_capture = self.load_capture(current_num)

        while selected_capture is None:
            key = self.key_pressed()

            if key == "left":
                current_num -= 1
                if current_num < CvCamera.min_cap_num:
                    current_num = CvCamera.min_cap_num
                    print("Camera failed to load! Camera number lower limit:", current_num)
                    continue
                while current_num in CvCamera.used_captures:
                    current_num -= 1

                current_capture = self.load_capture(current_num)

            elif key == "right":
                current_num += 1
                if CvCamera.max_cap_num is not None and current_num > CvCamera.max_cap_num:
                    print("Camera failed to load! Camera number upper limit:", current_num)
                    current_num = CvCamera.max_cap_num
                    continue

                while current_num in CvCamera.used_captures:
                    current_num += 1

                try:
                    current_capture = self.load_capture(current_num)
                    success, frame = current_capture.read()
                    cv2.imshow(selector_window_name, frame)
                except cv2.error:
                    print("Camera failed to load! Camera number upper limit:", current_num)
                    if current_num in CvCamera.captures:
                        current_capture.release()
                        del CvCamera.captures[current_num]
                    current_num -= 1
                    CvCamera.max_cap_num = current_num
                    current_capture = self.load_capture(current_num)

            elif key == "\n" or key == "\r":
                selected_capture = current_capture
                CvCamera.used_captures.add(current_num)
                print("Using capture #%s for %s" % (current_num, self.name))

            elif key == 'q':
                selected_capture = None
                break

            success, frame = current_capture.read()
            cv2.imshow(selector_window_name, frame)
            height, width = frame.shape[0:2]
        cv2.destroyWindow(selector_window_name)
        return selected_capture, height, width

    def load_capture(self, arg):
        if arg not in CvCamera.captures:
            print("Loading capture '%s'..." % arg, end="")
            CvCamera.captures[arg] = cv2.VideoCapture(arg)
            print("done")
        return CvCamera.captures[arg]

    def key_pressed(self, delay=1):
        if not self.enabled:
            return 255
        key = cv2.waitKey(delay) % 255
        if key != 255:
            if key in self.key_codes:
                self.key = self.key_codes[key]
            elif 0 <= key < 0x100:
                self.key = chr(key)
            else:
                print(("Unrecognized key: " + str(key)))
        else:
            self.key = key

        return self.key

    def start_recording(self, file_name=None, directory=None, **options):
        if self.running:
            self.recorder = CvVideoRecorder(file_name, directory, self.width, self.height)
            self.recorder.start()
            self.is_recording = True
        else:
            raise FileNotFoundError("Camera hasn't started running yet!")

    def stop_recording(self):
        if self.is_recording:
            self.recorder.close()

    def start(self):
        self.launch_camera()

    def run(self):
        while self.are_others_running():
            success, self.frame = self.capture.read()
            if not success:
                self.exit()
                raise EOFError("Failed to read the frame")

            if self.resize_frame and self.frame.shape[0:2] != (self.height, self.width):
                self.frame = cv2.resize(self.frame, (self.width, self.height))

            self.poll_for_fps()

            if self.is_recording:
                self.recorder.write(self.frame, self.fps)

            self.update()

    def update(self):
        pass

    def poll_for_fps(self):
        if self.prev_t is None:
            self.prev_t = time.time()
            return 0.0

        self.length_sec = time.time() - self.start_time
        self.fps = 1 / (time.time() - self.prev_t)
        self.fps_sum += self.fps
        self.num_frames += 1
        self.fps_avg = self.fps_sum / self.num_frames

        self.prev_t = time.time()

    def close(self):
        for cap_name, capture in CvCamera.captures.items():
            capture.release()
        CvCamera.captures = {}

        self.stop_recording()

        cv2.destroyWindow(self.name)
