import time

from flask import Response, render_template, request

from atlasbuggy.clock import Clock
from atlasbuggy.website import Website


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

        self.actuators = None
        self.camera = None
        self.cmdline = None
        self.pipeline = None

        self.show_orignal = True
        self.lights_are_on = False

        self.clock = None
        self.commands = None

    def take(self):
        self.actuators = self.streams["actuators"]
        self.camera = self.streams["camera"]
        self.cmdline = self.streams["cmdline"]
        self.pipeline = self.streams["pipeline"]

        self.show_orignal = not self.pipeline.enabled

        self.clock = Clock(float(self.camera.fps))

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
                   int(self.pipeline.autonomous_mode)),
            Button(["pause video", "unpause video"], ":toggle_camera", "toggle_camera_button",
                   "command_button toggles"),
            Button(["show original", "show pipeline"], ":toggle_pipeline", "toggle_pipeline_button",
                   "command_button toggles",
                   int(self.show_orignal)),

            Button("say hello!", "hello", "say hello button", "command_button speak"),
            Button("PANIC!!!", "alert", "alert button", "command_button speak"),
        )

    def start(self):
        self.clock.start()

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
                    return self.commands[command].switch_label(int(self.camera.paused))

                elif command == ":toggle_pipeline":
                    self.show_orignal = not self.show_orignal
                    self.pipeline.generate_bytes = not self.show_orignal
                    return self.commands[command].switch_label(int(self.show_orignal))

                elif command == ":toggle_lights":
                    self.lights_are_on = not self.lights_are_on
                    if self.lights_are_on:
                        self.cmdline.handle_input("white 255")
                    else:
                        self.cmdline.handle_input("white 15")

                    return self.commands[command].switch_label(int(self.lights_are_on))

                elif command == ":toggle_autonomy":
                    self.pipeline.autonomous_mode = not self.pipeline.autonomous_mode
                    return self.commands[command].switch_label(int(self.pipeline.autonomous_mode))
            else:
                self.cmdline.handle_input(command.replace("_", " "))
        return ""

    def video(self):
        """Video streaming generator function."""
        while True:
            if self.show_orignal:
                frame = self.camera.get_bytes_frame()
            else:
                frame = self.pipeline.bytes_frame
            if frame is not None:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

                if self.camera.paused:
                    time.sleep(0.25)
                self.clock.update()

    def video_feed(self):
        """Video streaming route. Put this in the src attribute of an img tag."""
        return Response(self.video(), mimetype='multipart/x-mixed-replace; boundary=frame')
