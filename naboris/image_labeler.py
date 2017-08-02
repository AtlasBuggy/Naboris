from atlasbuggy.camera.viewer import CameraViewer
from naboris.ui_elements import *


class ImageLabeler(CameraViewer):
    def __init__(self, enabled=True, log_level=None):
        super(ImageLabeler, self).__init__(enabled, log_level, draw_while_paused=True)

        self.cropped = None
        self.texture_service_tag = "texture"
        self.adjust_subscription(self.capture_tag, service_tag=self.texture_service_tag)

        categories = ["wood", "tile", "carpet", "wall_lip", "wall", "obstacle"]
        self.buttons = {}
        self.textboxes = {}

        button_x = 20
        button_y = 100
        for category in categories:
            text_width, text_height, baseline = TextBox.get_text_size(category)
            text_height += 20
            text_width += 20

            button = RectangleButton([(button_x, button_y - text_height),
                                      (button_x + text_width, button_y)])
            text = TextBox(category, button.center_pt)

            self.buttons[category] = button
            self.textboxes[category] = text

            button_y += 50

        cv2.setMouseCallback(self.name, self.mouse_callback)

    def get_frame_from_feed(self):
        frame, self.cropped = self.capture_feed.get()
        return frame

    def draw(self, frame):
        for button in self.buttons.values():
            button.draw(frame)

        for textbox in self.textboxes.values():
            textbox.draw(frame)

        return frame

    def mouse_callback(self, event, x, y, flags, param):
        for category, button in self.buttons.items():
            if button.update(event, x, y):
                self.capture.write_training_image(category, self.cropped)

    def key_down(self, key):
        if key == 'q':
            self.exit()
        elif key == ' ':
            self.toggle_pause()
