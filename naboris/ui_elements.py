import cv2
import math


class TextBox:
    CENTER = (0, 0)
    TOP_LEFT = (-1, -1)
    TOP_RIGHT = (1, -1)
    BOTTOM_LEFT = (-1, 1)
    BOTTOM_RIGHT = (1, 1)

    DEFAULT_FONT = cv2.FONT_HERSHEY_COMPLEX
    DEFAULT_FONT_SCALE = 0.5
    DEFAULT_FONT_THICKNESS = 1

    def __init__(self, text, position, margin=(0, 0), color=(0, 0, 0), alignment=CENTER, font=DEFAULT_FONT,
                 font_scale=DEFAULT_FONT_SCALE, font_thickness=DEFAULT_FONT_THICKNESS, background_color=None):
        self.color = color
        self.position = list(position)
        self.margin = margin
        self.font = font
        self.font_scale = font_scale
        self.font_thickness = font_thickness
        self.background_color = background_color
        self.alignment = alignment

        if self.background_color is None:
            self.current_color = None
            self.current_alpha = None
        else:
            self.current_color = self.background_color[0:3][::-1]
            self.current_alpha = self.background_color[3]

        self.set_text(text)
        self.set_alignment(alignment)

    def set_text(self, text):
        self.text = text
        (self.width, self.height), self.base_line = cv2.getTextSize(
            self.text, self.font, self.font_scale, self.font_thickness
        )
        self.update_background()

    @staticmethod
    def get_text_size(text, font=DEFAULT_FONT, font_scale=DEFAULT_FONT_SCALE, font_thickness=DEFAULT_FONT_THICKNESS):
        (width, height), base_line = cv2.getTextSize(
            text, font, font_scale, font_thickness
        )
        return width, height, base_line

    def set_alignment(self, alignment):
        self.alignment = alignment

        self.set_point(self.position)

    def set_point(self, point):
        self.position[0] = point[0]
        self.position[1] = point[1]

        self.text_x = 0
        self.text_y = 0

        if self.alignment[0] == -1:
            self.text_x = 0
        elif self.alignment[0] == 0:
            self.text_x = -self.width // 2
        elif self.alignment[0] == 1:
            self.text_x = -self.width

        if self.alignment[1] == -1:
            self.text_y = self.height
        elif self.alignment[1] == 0:
            self.text_y = self.height // 2
        elif self.alignment[1] == 1:
            self.text_y = 0

        self.text_x += self.position[0]
        self.text_y += self.position[1]

        self.update_background()

    def update_background(self):
        self.x1 = 0
        self.y1 = 0
        self.x2 = 0
        self.y2 = 0

        if self.alignment[0] == -1:
            self.x1 = -self.margin[0]
            self.x2 = self.width + self.margin[0]
        elif self.alignment[0] == 0:
            self.x1 = -self.margin[0] - self.width // 2
            self.x2 = self.margin[0] + self.width // 2
        elif self.alignment[0] == 1:
            self.x1 = self.margin[0] + self.width
            self.x2 = -self.margin[0]

        if self.alignment[1] == -1:
            self.y1 = self.margin[1] + self.height
            self.y2 = -self.margin[1]
        elif self.alignment[1] == 0:
            self.y1 = self.margin[1] + self.height // 2
            self.y2 = -self.margin[1] - self.height // 2
        elif self.alignment[1] == 1:
            self.y1 = -self.margin[1]
            self.y2 = self.margin[1] + self.height

        self.x1 += self.position[0]
        self.y1 += self.position[1]
        self.x2 += self.position[0]
        self.y2 += self.position[1]

    def draw(self, frame):
        # cv2.circle(frame, (self.x1, self.y1), 3, (255, 0, 0), -1)
        # cv2.circle(frame, (self.x2, self.y2), 3, (0, 0, 255), -1)
        if self.background_color is not None:
            overlay = frame.copy()

            cv2.rectangle(overlay,
                          (self.x1, self.y1),
                          (self.x2, self.y2),
                          self.current_color, -1)
            cv2.addWeighted(overlay, self.current_alpha, frame, 1 - self.current_alpha, 0, frame)

        cv2.putText(
            frame, self.text, (self.text_x, self.text_y), self.font, self.font_scale, self.color, self.font_thickness
        )


class Button:
    UNSELECTED = 0
    HOVER = 1
    SELECTED = 2
    DISABLED = 3

    def __init__(self, points, unselected_color=None, hover_color=None, selected_color=None, disabled_color=None,
                 thickness=-1, mouse_up_event=True):
        self.enabled = True
        self.points = points
        self.state = Button.UNSELECTED
        self.thickness = thickness

        if unselected_color is None:
            unselected_color = (225, 225, 225, 0.85)
        if hover_color is None:
            hover_color = (194, 194, 194, 0.85)
        if selected_color is None:
            selected_color = (153, 153, 153, 0.85)
        if disabled_color is None:
            disabled_color = (240, 240, 240, 0.85)

        self.colors = [unselected_color, hover_color, selected_color, disabled_color]

        self.unselected_color = unselected_color
        self.hover_color = hover_color
        self.selected_color = selected_color

        self.mouse_up_event = mouse_up_event

        self.set_state(self.state)

    def set_state(self, state):
        self.state = state
        self.set_color(self.colors[self.state])

    def set_color(self, color):
        self.current_color = color[0:3][::-1]
        if len(color) == 4:
            self.current_alpha = color[3]
        else:
            self.current_alpha = 1

    def is_selected(self, x, y):
        pass

    def draw(self, frame):
        pass

    def update(self, event, x, y):
        if self.enabled:
            if event == cv2.EVENT_LBUTTONDOWN:
                if self.is_selected(x, y):
                    self.set_state(Button.SELECTED)
                    if not self.mouse_up_event:
                        return True
            elif event == cv2.EVENT_LBUTTONUP:
                if self.is_selected(x, y):
                    self.set_state(Button.HOVER)
                    if self.mouse_up_event:
                        return True
            else:
                if self.is_selected(x, y):
                    self.set_state(Button.HOVER)
                else:
                    self.set_state(Button.UNSELECTED)

        return False

    def disable_button(self):
        self.set_state(Button.DISABLED)
        self.enabled = False

    def enable_button(self):
        self.set_state(Button.UNSELECTED)
        self.enabled = True


class RectangleButton(Button):
    def __init__(self, *args, **kwargs):
        super(RectangleButton, self).__init__(*args, **kwargs)
        self.set_points(self.points)

    def set_points(self, points):
        self.top_left_pt = self.points[0]
        self.bottom_right_pt = self.points[1]

        self.x_left = self.top_left_pt[0]
        self.y_top = self.top_left_pt[1]

        self.x_right = self.bottom_right_pt[0]
        self.y_bottom = self.bottom_right_pt[1]

        self.center_pt = (self.x_right - self.x_left) // 2 + self.x_left, (self.y_bottom - self.y_top) // 2 + self.y_top

        self.x_center = self.center_pt[0]
        self.y_center = self.center_pt[1]

        assert self.x_right > self.x_left
        assert self.y_bottom > self.y_top

    def is_selected(self, x, y):
        return (self.x_left <= x <= self.x_right and
                self.y_top <= y <= self.y_bottom)

    def draw(self, frame):
        if self.current_alpha != 1:
            overlay = frame.copy()
            cv2.rectangle(overlay, self.top_left_pt, self.bottom_right_pt, self.current_color, thickness=self.thickness)
            cv2.addWeighted(overlay, self.current_alpha, frame, 1 - self.current_alpha, 0, frame)
        else:
            cv2.rectangle(frame, self.top_left_pt, self.bottom_right_pt, self.current_color, thickness=self.thickness)


class CircleButton(Button):
    def __init__(self, point, radius, *args, **kwargs):
        super(CircleButton, self).__init__(point, *args, **kwargs)
        self.set_point(point, radius)

    def set_point(self, point, radius=None):
        if radius is not None:
            self.radius = radius
        self.x = point[0]
        self.y = point[1]

    def is_selected(self, x, y):
        dist = math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)
        return dist <= self.radius

    def draw(self, frame):
        if self.current_alpha != 1:
            overlay = frame.copy()
            cv2.circle(overlay, self.points, self.radius, self.current_color, thickness=self.thickness)
            cv2.addWeighted(overlay, self.current_alpha, frame, 1 - self.current_alpha, 0, frame)
        else:
            cv2.circle(frame, self.points, self.radius, self.current_color, thickness=self.thickness)
