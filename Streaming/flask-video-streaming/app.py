#!/usr/bin/env python
import time
from multiprocessing import Process, Event
from flask import Flask, render_template, Response

# emulated camera
from camera import Camera

# Raspberry Pi camera module (requires picamera package)
# from camera_pi import Camera

app = Flask(__name__)


@app.route('/')  # URL that triggers this function
def index():
    """Video streaming home page."""
    return render_template('index.html')


def gen(camera):
    """Video streaming generator function."""
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(Camera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

class Website(Process):
    def __init__(self):
        super(Website, self).__init__(target=self.run)

    def run(self):
        app.run(host='0.0.0.0', debug=True, threaded=True)

Website().start()
