import cv2
import time
import mpld3

from flask import Response, render_template, request, json

from atlasbuggy.extras.website import Website
from atlasbuggy.subscriptions import *


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
        # website hosted under http://naboris:5000
        # check /etc/hosts for host names

        super(NaborisWebsite, self).__init__(
            template_folder, static_folder, enabled=enabled,
            # app_params=dict(
            #     port=80
            # )
        )

        # self.app.add_url_rule("/lights", view_func=self.lights, methods=['POST'])
        self.app.add_url_rule("/cmd", view_func=self.command_response, methods=['POST'])
        self.app.add_url_rule("/video_feed", view_func=self.video_feed)
        self.app.add_url_rule("/plot", view_func=self.plot, methods=['POST'])

        self.show_orignal = True
        self.lights_are_on = False
        self.autonomous_mode = False

        self.commands = None

        self.camera_tag = "camera"
        self.pipeline_tag = "pipeline"
        self.cmd_tag = "cmdline"
        self.plotter_tag = "plotter"

        self.require_subscription(self.camera_tag, Update)
        self.require_subscription(self.pipeline_tag, Update)
        self.require_subscription(self.cmd_tag, Subscription)
        self.require_subscription(self.plotter_tag, Subscription, is_suggestion=True)

        self.camera = None
        self.cmdline = None
        self.pipeline = None
        self.plotter = None

        self.camera_subscription = None
        self.pipeline_subscription = None

        self.camera_feed = None
        self.pipeline_feed = None

        self.frame_feed = None

    def take(self, subscriptions):
        self.camera = subscriptions[self.camera_tag].get_stream()
        self.pipeline = subscriptions[self.pipeline_tag].get_stream()
        self.cmdline = subscriptions[self.cmd_tag].get_stream()
        if self.plotter_tag in subscriptions:
            self.plotter = subscriptions[self.plotter_tag].get_stream()

        self.camera_subscription = subscriptions[self.camera_tag]
        self.pipeline_subscription = subscriptions[self.pipeline_tag]

        self.camera_feed = subscriptions[self.camera_tag].get_feed()
        self.pipeline_feed = subscriptions[self.pipeline_tag].get_feed()

        self.show_orignal = not self.pipeline.enabled
        self.update_frame_source()

        self.autonomous_mode = False

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
            Button(["autonomous", "manual"], ":toggle_autonomy", "toggle_autonomy_button", "command_button toggles",
                   int(self.autonomous_mode)),
            Button(["pause video", "unpause video"], ":toggle_camera", "toggle_camera_button",
                   "command_button toggles"),
            Button(["show original", "show pipeline"], ":toggle_pipeline", "toggle_pipeline_button",
                   "command_button toggles", int(self.show_orignal)),
            Button(["start recording", "stop recording"], ":toggle_recording", "toggle_recording_button",
                   "command_button toggles", int(self.is_recording())),
            Button("adjust filter", ":adjust_filter", "adjust_filter_button", "command_button toggles"),

            Button("say hello!", "hello", "say hello button", "command_button speak"),
            Button("PANIC!!!", "alert", "alert button", "command_button speak"),
        )

    def update_frame_source(self):
        if self.pipeline.enabled and not self.show_orignal:
            self.pipeline_subscription.enabled = True
            self.camera_subscription.enabled = False
            self.frame_feed = self.pipeline_feed
        else:
            self.pipeline_subscription.enabled = False
            self.camera_subscription.enabled = True
            self.frame_feed = self.camera_feed

    def is_recording(self):
        if hasattr(self.camera, "is_recording"):
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
                    self.camera.paused = not self.camera.paused
                    if self.camera.paused:
                        self.pipeline_subscription.enabled = False
                        self.camera_subscription.enabled = False
                    else:
                        self.update_frame_source()

                    return self.commands[command].switch_label(int(self.camera.paused))

                elif command == ":toggle_pipeline":
                    self.show_orignal = not self.show_orignal
                    self.update_frame_source()

                    return self.commands[command].switch_label(int(self.show_orignal))

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

                elif command == ":adjust_filter":
                    self.pipeline.adjust_filter()
            else:
                self.cmdline.handle_input(command.replace("_", " "))
        return ""

    def video(self):
        """Video streaming generator function."""
        if self.pipeline.enabled and not self.show_orignal:
            self.pipeline_subscription.enabled = True
        else:
            self.camera_subscription.enabled = True

        while True:
            while not self.frame_feed.empty():
                frame = self.frame_feed.get()
                if frame is not None:
                    if self.pipeline_subscription.enabled and type(frame) == tuple:
                        frame = frame[0]
                    bytes_frame = self.numpy_to_bytes(frame)
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + bytes_frame + b'\r\n')

                    if self.camera.paused:
                        time.sleep(0.25)
                    time.sleep(1 / self.camera.fps)

    def update_plot(self):
        while True:
            time.sleep(0.01)
            yield mpld3.fig_to_html(self.plotter.fig)

    def plot(self):
        if self.is_subscribed(self.plotter):
            return Response(self.update_plot(), mimetype='text/html')
        else:
            return ""
        # return mpld3.fig_to_html(self.plotter.fig)

    def video_feed(self):
        """Video streaming route. Put this in the src attribute of an img tag."""
        return Response(self.video(), mimetype='multipart/x-mixed-replace; boundary=frame')

    @staticmethod
    def numpy_to_bytes(frame):
        return cv2.imencode(".jpg", frame)[1].tostring()
