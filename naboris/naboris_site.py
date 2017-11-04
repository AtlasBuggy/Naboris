import cv2
import time
import math
import asyncio

from flask import Response, render_template, request

from atlasbuggy.opencv.messages import ImageMessage

from .website import Website

class Button:
    def __init__(self, labels, command, button_id, group, current_label=0):
        self.labels = labels
        self.command = command
        self.button_id = button_id
        self.group = group
        if type(labels) == str:
            self.current_label = self.labels
        else:
            self.current_label = self.labels[current_label]

    def switch_label(self, index):
        if type(self.labels) == str:
            return self.current_label
        else:
            self.current_label = self.labels[index]
            return self.current_label


class ButtonCollection:
    def __init__(self, *buttons):
        self.buttons = buttons

        self.dict_buttons = {}
        for button in self.buttons:
            self.dict_buttons[button.command] = button

        self.grouped_buttons = {}
        for button in self.buttons:
            if button.group not in self.grouped_buttons:
                self.grouped_buttons[button.group] = [button]
            else:
                self.grouped_buttons[button.group].append(button)

    def get_group(self, group):
        for button in self.grouped_buttons[group]:
            yield button.current_label, button.command, button.button_id, button.group

    def __getitem__(self, item):
        return self.dict_buttons[item]


class NaborisWebsite(Website):
    def __init__(self, template_folder, static_folder, enabled=True):
        # website hosted under http://192.168.200.1:5000
        # check /etc/hosts for host names

        super(NaborisWebsite, self).__init__(
            template_folder, static_folder, enabled=enabled,
        )

        self.app.add_url_rule("/cmd", view_func=self.command_response, methods=['POST'])
        self.app.add_url_rule("/video_feed", view_func=self.video_feed)
        self.app.add_url_rule("/angle", view_func=self.post_angle, methods=['GET'])

        self.show_orignal = True
        self.lights_are_on = False

        self.commands = None

        self.camera_tag = "camera"
        self.cmd_tag = "cmdline"
        self.bno055_tag = "bno055"

        self.camera_sub = self.define_subscription(self.camera_tag, message_type=ImageMessage,
                                                   required_attributes=("fps",), required_methods=("get_pause",))
        self.cmd_sub = self.define_subscription(self.cmd_tag, required_attributes=("handle_input",), queue_size=None)
        self.bno055_sub = self.define_subscription(self.bno055_tag, service="bno055", queue_size=1, is_required=False)

        self.camera = None
        self.cmdline = None
        self.bno055_queue = None

        self.camera_queue = None
        self.camera_has_attributes = False

        self.image_message = None
        self.bno055_message = None

    def take(self):
        self.camera = self.camera_sub.get_producer()
        self.camera_queue = self.camera_sub.get_queue()
        if self.is_subscribed(self.bno055_tag):
            self.bno055_queue = self.bno055_sub.get_queue()

        self.cmdline = self.cmd_sub.get_producer()

        if self.producer_has_attributes(self.camera_sub, "is_recording"):
            self.camera_has_attributes = True

        self.commands = ButtonCollection(
            Button("spin left", "l", "spin_left_button", "command_button drive"),
            Button("spin right", "r", "spin_right_button", "command_button drive"),
            Button("drive forward", "d_0", "drive_forward_button", "command_button drive"),
            Button("drive left", "d_90_150", "drive_left_button", "command_button drive"),
            Button("drive backward", "d_180", "drive_backward_button", "command_button drive"),
            Button("drive right", "d_270_150", "drive_right_button", "command_button drive"),
            Button("stop", "s", "stop_driving_button", "command_button drive"),

            Button(["lights on", "lights off"], ":toggle_lights", "toggle_lights_button", "command_button toggles",
                   int(self.lights_are_on)),
            Button("take a photo", "photo", "take_a_photo_button", "command_button toggles"),
            Button(["pause video", "unpause video"], ":toggle_camera", "toggle_camera_button",
                   "command_button toggles"),
            Button(["start recording", "stop recording"], ":toggle_recording", "toggle_recording_button",
                   "command_button toggles", int(self.is_recording())),

            Button("say hello!", "hello", "say hello button", "command_button speak"),
            Button("PANIC!!!", "alert", "alert button", "command_button speak"),
        )

    def is_recording(self):
        if self.camera_has_attributes:
            return self.camera.is_recording
        else:
            return False

    def index(self):
        return render_template('index.html', commands=self.commands)

    def command_response(self):
        command = request.args.get('command')
        return self.process_command(command), 200, {'Content-Type': 'text/plain'}

    def process_command(self, command):
        if len(command) > 0:
            if command[0] == ":":
                if command == ":toggle_camera":
                    self.camera_sub.enabled = self.camera.paused
                    self.camera.paused = not self.camera.paused

                    return self.commands[command].switch_label(int(self.camera.paused))

                elif command == ":toggle_lights":
                    self.lights_are_on = not self.lights_are_on
                    if self.lights_are_on:
                        self.cmdline.handle_input("white 255")
                    else:
                        self.cmdline.handle_input("white 15")

                    return self.commands[command].switch_label(int(self.lights_are_on))

                elif command == ":toggle_autonomy":
                    self.autonomous_mode = not self.autonomous_mode
                    if self.autonomous_mode:
                        self.cmdline.set_autonomous()
                    else:
                        self.cmdline.set_manual()

                    return self.commands[command].switch_label(int(self.autonomous_mode))

                elif command == ":toggle_recording":
                    if not self.is_recording():
                        self.cmdline.handle_input("start_video")
                    else:
                        self.cmdline.handle_input("stop_video")
                    return self.commands[command].switch_label(int(self.is_recording()))

            else:
                self.cmdline.handle_input(command.replace("_", " "))
        return ""

    async def loop(self):
        while True:
            while not self.camera_queue.empty():
                image_message = await self.camera_queue.get()
                self.image_message = image_message

            if self.is_subscribed(self.bno055_tag):
                bno055_message = await self.bno055_queue.get()
                self.bno055_message = bno055_message

            await asyncio.sleep(0.5 / self.camera.fps)

    def angle_generator(self):
        prev_angle = 0
        while True:
            if self.bno055_message is not None:
                angle = int(math.degrees(self.bno055_message.euler.z))
                if angle != prev_angle:
                    yield ("%s\n" % angle).encode()
                prev_angle = angle

                self.bno055_message = None
            time.sleep(0.01)

    def post_angle(self):
        return Response(self.angle_generator(), mimetype='text/plain')

    def video(self):
        """Video streaming generator function."""
        while True:
            if self.image_message is not None:
                bytes_frame = self.image_message.numpy_to_bytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + bytes_frame + b'\r\n')

                self.image_message = None
            time.sleep(0.5 / self.camera.fps)
            if self.camera.get_pause():
                time.sleep(0.25)

    def video_feed(self):
        """Video streaming route. Put this in the src attribute of an img tag."""
        return Response(self.video(), mimetype='multipart/x-mixed-replace; boundary=frame')
