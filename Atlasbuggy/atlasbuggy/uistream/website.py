from flask import Flask, render_template, Response
from camera_pi import Camera
from atlasbuggy.uistream import UIstream
import threading
import asyncio

class Website(UIstream):
    def __init__(self, name, template_folder):
        self.app = Flask(__name__, template_folder=template_folder)
        self.app.add_url_rule("/", "index", self.index)
        self.app.add_url_rule("/video_feed", view_func=self.video_feed)

        super(Website, self).__init__(name, True, False, True)

    def index(self):
        """
        app.add_url_rule('/', 'hello', hello_world)

        Is the same as:

        @app.route('/hello')
        def hello_world():
           return 'hello world'
        """
        return render_template('index.html')

    def gen(self, camera):
        """Video streaming generator function."""
        while True:
            frame = camera.get_frame()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    def video_feed(self):
        """Video streaming route. Put this in the src attribute of an img tag."""
        return Response(self.gen(Camera()),
                        mimetype='multipart/x-mixed-replace; boundary=frame')

    def run(self):
        self.app.run(host='0.0.0.0')#, debug=True, threaded=True)
