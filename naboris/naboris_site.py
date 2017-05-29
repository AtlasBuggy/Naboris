import time
from atlasbuggy.filestream import BaseFile
from flask import Flask, render_template, Response, request

from atlasbuggy.uistream.website import Website


class NaborisWebsite(Website):
    def __init__(self, template_folder, static_folder, actuators, camera, pipeline, cmdline, enabled=True):
        # website hosted under http://naboris:5000
        # check /etc/hosts for host names

        super(NaborisWebsite, self).__init__(template_folder, static_folder, enabled=enabled)

        # self.app.add_url_rule("/lights", view_func=self.lights, methods=['POST'])
        self.app.add_url_rule("/cmd", view_func=self.command_response, methods=['POST'])
        self.app.add_url_rule("/video_feed", view_func=self.video_feed)

        self.actuators = actuators
        self.camera = camera
        self.cmdline = cmdline
        self.pipeline = pipeline

        self.show_orignal = True
        self.lights_are_on = False

        self.delay = 1.5 / float(self.camera.fps)
        self.prev_time = time.time()
        print("camera framerate:", self.camera.fps)

        self.commands = {
            "spin left": "l",
            "spin right": "r",
            "drive forward": "d_0",
            "drive left": "d_90",
            "drive backward": "d_180",
            "drive right": "d_270",
            "stop": "s",
            "lights on": "toggle_lights",
            "say hello!": "hello",
            "PANIC!!!": "alert",
            "pause video": "cam_toggle",
            "show pipeline": "pipeline_toggle",
        }

    def index(self):
        return render_template('index.html', commands=self.commands)

    def command_response(self):
        command = request.args.get('command')
        return self.process_command(command), 200, {'Content-Type': 'text/plain'}

    def process_command(self, command):
        if command == "cam_toggle":
            self.camera.paused = not self.camera.paused
            return "unpause video" if self.camera.paused else "pause video"

        elif command == "pipeline_toggle":
            self.show_orignal = not self.show_orignal
            return "show pipeline" if self.show_orignal else "show original"

        elif command == "toggle_lights":
            self.lights_are_on = not self.lights_are_on
            if self.lights_are_on:
                response_text = "lights off"
                self.cmdline.handle_input("white 255")
            else:
                response_text = "lights on"
                self.cmdline.handle_input("white 15")

            return response_text
        else:
            self.cmdline.handle_input(command.replace("_", " "))
            return ""

    def video(self):
        """Video streaming generator function."""
        frame = None
        while True:
            frame = self.camera.raw_frame

            if not self.show_orignal:
                self.pipeline.frame = self.camera.get_frame()
                self.pipeline.update()
                frame = self.pipeline.raw_frame()

            if frame is not None:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                time.sleep(self.delay)

    def video_feed(self):
        """Video streaming route. Put this in the src attribute of an img tag."""
        self.prev_time = time.time()
        return Response(self.video(), mimetype='multipart/x-mixed-replace; boundary=frame')

    def pause_camera(self):
        self.camera.paused = True

    def unpause_camera(self):
        self.camera.paused = False
