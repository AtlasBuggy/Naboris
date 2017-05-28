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
            "lights on": "white_255",
            "lights off": "white_15",
            "say hello!": "hello",
            "PANIC!!!": "alert",
            "pause video": "pause",
            "unpause video": "unpause",
        }

    def index(self):
        return render_template('index.html', commands=self.commands)

    def command_response(self):
        command = request.args.get('command').replace("_", " ")
        if command == "pause":
            self.pause_camera()
        elif command == "unpause":
            self.unpause_camera()
        else:
            self.cmdline.handle_input(command)
        return str(command), 200, {'Content-Type': 'text/plain'}

    def video(self):
        """Video streaming generator function."""
        while True:
            frame = self.pipeline.raw_frame()
            if (time.time() - self.prev_time) > self.delay:
                self.prev_time = time.time()
                if frame is not None:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    def video_feed(self):
        """Video streaming route. Put this in the src attribute of an img tag."""
        self.prev_time = time.time()
        return Response(self.video(), mimetype='multipart/x-mixed-replace; boundary=frame')

    def pause_camera(self):
        self.camera.paused = True

    def unpause_camera(self):
        self.camera.paused = False
