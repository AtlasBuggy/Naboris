from flask import Flask, render_template, Response, request
from atlasbuggy.uistream.website import Website


class NaborisWebsite(Website):
    def __init__(self, template_folder, actuators, camera, enabled=True):
        super(NaborisWebsite, self).__init__(template_folder, enabled)

        self.app.add_url_rule("/video_feed", view_func=self.video_feed)
        self.app.add_url_rule("/lights", view_func=self.lights, methods=['POST'])
        # self.app.add_url_rule("/lights_off", view_func=self.lights_off)
        self.actuators = actuators
        self.camera = camera

    def index(self):
        return render_template('index.html')

    def gen(self):
        """Video streaming generator function."""
        while True:
            frame = self.camera.get_frame()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    def video_feed(self):
        """Video streaming route. Put this in the src attribute of an img tag."""
        return Response(self.gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

    def set_lights(self, value):
        self.actuators.set_all_leds(value, value, value)

    def lights(self):
        if request.form["lights"] == "on":
            self.set_lights(255)
        else:
            self.set_lights(15)
        return '', 200
