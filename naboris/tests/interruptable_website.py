import time
from threading import Thread, Event
from flask import Flask, request

class LoopThread(Thread):
    def __init__(self, stop_event, interrupt_event):
        self.stop_event = stop_event
        self.interrupt_event = interrupt_event
        Thread.__init__(self)

    def run(self):
        while not self.stop_event.is_set():
            self.loop_process()
            if self.interrupt_event.is_set():
                self.interrupted_process()
                self.interrupt_event.clear()

    def loop_process(self):
        print("Processing!")
        time.sleep(3)

    def interrupted_process(self):
        print("Interrupted!")

STOP_EVENT = Event()
INTERRUPT_EVENT = Event()
thread = LoopThread(STOP_EVENT, INTERRUPT_EVENT)

app = Flask(__name__)

@app.route("/interrupt")
def interrupt():
    INTERRUPT_EVENT.set()
    return "OK", 200

# http://flask.pocoo.org/snippets/67/
def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

@app.route("/shutdown")
def shutdown():
    STOP_EVENT.set()
    thread.join()
    shutdown_server()
    return "OK", 200


thread.start()
app.run(host='0.0.0.0', debug=True, threaded=True)
