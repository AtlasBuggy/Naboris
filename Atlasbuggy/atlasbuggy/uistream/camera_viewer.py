import cv2
import asyncio
from atlasbuggy.datastream import DataStream
from atlasbuggy import get_platform


class CameraViewer(DataStream):
    def __init__(self, capture, enabled=True, debug=False, name=None, enable_slider=False):
        super(CameraViewer, self).__init__(enabled, debug, False, True, name)

        self.capture = capture
        if self.enabled:
            cv2.namedWindow(self.capture.name)

        self.key = -1
        self.slider_pos = 0
        self.slider_name = "frame:"
        self.enable_slider = enable_slider

        self.slider_ticks = int(self.capture.capture.get(cv2.CAP_PROP_FRAME_WIDTH) // 3)
        if self.slider_ticks > self.capture.num_frames:
            self.slider_ticks = self.capture.num_frames

        if self.enabled and self.enable_slider:
            cv2.createTrackbar(self.slider_name, self.capture.name, 0, self.slider_ticks, self.on_slider)

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

    async def run(self):
        if not self.enabled:
            return
        while self.all_running():
            self.show_frame()
            self.update()
            await asyncio.sleep(0.1 / self.capture.fps)

    def update(self):
        pass

    def _on_slider(self, slider_index):
        slider_pos = int(slider_index * self.capture.num_frames / self.slider_ticks)
        if abs(slider_pos - self.capture.current_pos()) > 1:
            self.capture.set_frame(slider_pos)
            # self.show_frame()
            self.slider_pos = slider_index
            self.on_slider(slider_index)

    def on_slider(self, slider_index):
        pass

    def show_frame(self):
        """
        Display the frame in the Capture's window using cv2.imshow
        :param frame: A numpy array containing the image to be displayed
                (shape = (height, width, 3))
        :return: None
        """
        frame = self.capture.get_frame()

        if frame is None:
            return

        self.key_pressed()
        cv2.imshow(self.capture.name, frame)

    def key_pressed(self, delay=1):
        if not self.enabled:
            return -1
        key = cv2.waitKey(delay)
        if key > -1:
            if key in self.key_codes:
                self.key = self.key_codes[key]
            elif 0 <= key < 0x100:
                self.key = chr(key)
            else:
                print(("Unrecognized key: " + str(key)))

            self.key_callback(self.key)
        else:
            self.key = key

    def key_callback(self, key):
        if key == 'q':
            self.exit()

    def close(self):
        cv2.destroyWindow(self.name)
