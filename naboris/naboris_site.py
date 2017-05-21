from flask import Flask, render_template, Response, request
from atlasbuggy.uistream.website import Website
import time


class NaborisWebsite(Website):
    def __init__(self, template_folder, actuators, camera, cmdline, enabled=True):
        # website hosted under http://naboris:5000
        # check /etc/hosts for host names
        super(NaborisWebsite, self).__init__("naboris website", template_folder, enabled)

        # self.app.add_url_rule("/lights", view_func=self.lights, methods=['POST'])
        self.app.add_url_rule("/cmd", view_func=self.command_response, methods=['POST'])
        self.app.add_url_rule("/video_feed", view_func=self.video_feed)

        self.actuators = actuators
        self.camera = camera
        self.cmdline = cmdline

        self.camera_paused = False
        self.fps = 30

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
        frame = None
        while True:
            if self.camera_paused:
                time.sleep(0.1)
            else:
                frame = self.camera.get_frame()
                if frame is not None:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                    time.sleep(1 / self.fps)

    def video_feed(self):
        """Video streaming route. Put this in the src attribute of an img tag."""
        return Response(self.video(), mimetype='multipart/x-mixed-replace; boundary=frame')

    def pause_camera(self):
        self.camera_paused = True
        self.camera.paused = True

    def unpause_camera(self):
        self.camera_paused = False
        self.camera.paused = False

    # def set_lights(self, value):
    #     self.actuators.set_all_leds(value, value, value)
    #
    # def lights(self):
    #     if request.form["lights"] == "on":
    #         self.set_lights(255)
    #     else:
    #         self.set_lights(15)
    #     return '', 200
