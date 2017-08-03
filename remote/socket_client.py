import cv2
import json
import time
from threading import Lock
import numpy as np
from http.client import HTTPConnection

from atlasbuggy import ThreadedStream
from atlasbuggy.extras.cmdline import CommandLine
from atlasbuggy.subscriptions import *


class NaborisSocketClient(ThreadedStream):
    def __init__(self, address=("0.0.0.0", 5000), enabled=True, log_level=None):
        super(NaborisSocketClient, self).__init__(enabled, log_level)
        self.address = address

        self.buffer = b''

        self.width = None
        self.height = None
        self.num_frames = 0
        self.current_frame_num = 0

        self.reader = None
        self.writer = None

        self.prev_time = 0.0

        # self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection = None
        self.response_lock = Lock()

    def set_frame(self):
        pass

    def set_pause(self):
        pass

    def get_pause(self):
        return False

    def start(self):
        # self.socket.connect(self.address)
        # self.socket.send(b"GET /video_feed HTTP/1.0\n\n")
        self.connection = HTTPConnection("%s:%s" % (self.address[0], self.address[1]))

    def recv(self, response, chunk_size=1024):
        buf = response.read(chunk_size)
        while buf:
            yield buf
            with self.response_lock:
                buf = response.read(chunk_size)

    def run(self):
        headers = {'Content-type': 'image/jpeg'}
        self.connection.request("GET", "/video_feed", headers=headers)
        response = self.connection.getresponse()

        for resp in self.recv(response):
            if not self.is_running():
                return

            # resp = self.socket.recv(1024)

            if len(resp) == 0:
                return

            self.buffer += resp
            response_1 = self.buffer.find(b'\xff\xd8')
            response_2 = self.buffer.find(b'\xff\xd9')

            if response_1 != -1 and response_2 != -1:
                jpg = self.buffer[response_1:response_2 + 2]
                self.buffer = self.buffer[response_2 + 2:]
                image = self.to_image(jpg)

                self.post(image)

                self.current_frame_num += 1
                self.num_frames += 1
                print(self.num_frames, self.dt() - self.prev_time)
                self.prev_time = self.dt()
            time.sleep(0.001)

    def send_command(self, command):
        with self.response_lock:
            print("sending: %s" % command)
            headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
            self.connection.request("POST", "/cmd?command=" + str(command), json.dumps(""), headers)
            response = self.connection.getresponse()
            if response.status != 200:
                raise RuntimeError("Response was not OK: %s, %s" % (response.status, response.reason))

    def to_image(self, byte_stream):
        return cv2.imdecode(np.fromstring(byte_stream, dtype=np.uint8), 1)

    def stop(self):
        if self.reader is not None:
            self.reader.close()
        if self.writer is not None:
            self.writer.close()


class CLI(CommandLine):
    def __init__(self, enabled=True):
        super(CLI, self).__init__(enabled)

        self.client = None
        self.client_tag = "client"
        self.require_subscription(self.client_tag, Subscription, NaborisSocketClient)

    def take(self, subscriptions):
        self.client = self.subscriptions[self.client_tag].get_stream()

    def handle_input(self, line):
        if line == "q":
            self.exit()
        else:
            self.client.send_command(line)


class Commander(ThreadedStream):
    def __init__(self, enabled=True):
        super(Commander, self).__init__(enabled)

        self.pipeline_feed = None
        self.pipeline_tag = "pipeline"
        self.results_service_tag = "results"
        self.require_subscription(self.pipeline_tag, Update, service_tag=self.results_service_tag)

        self.client = None
        self.client_tag = "client"
        self.require_subscription(self.client_tag, Subscription, NaborisSocketClient)

        self.good_labels = ["wood", "tile", "carpet"]
        self.bad_labels = ["walllip", "wall", "obstacle"]

    def take(self, subscriptions):
        self.client = self.subscriptions[self.client_tag].get_stream()
        self.pipeline_feed = self.subscriptions[self.pipeline_tag].get_feed()

    def run(self):
        while self.is_running():
            while not self.pipeline_feed.empty():
                prediction_label, prediction_value = self.pipeline_feed.get()

                if prediction_label in self.good_labels:
                    self.client.send_command("d_0_100")
                elif prediction_label in self.bad_labels:
                    self.client.send_command("s")
                    # spin_direction = np.random.choice([150, -150], 1, p=[0.75, 0.25])
                    self.client.send_command("l")
                    # self.client.send_command("look")
                time.sleep(0.01)


# import cv2
# import numpy as np
# import socket
#
# address = ("0.0.0.0", 5000)
#
# # Set up a TCP/IP socket
# s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#
# # Connect as client to a selected server
# # on a specified port
# s.connect(address)
#
# # Protocol exchange - sends and receives
# s.send(b"GET /video_feed HTTP/1.0\n\n")
#
# buffer = b''
#
# window_name = "stream"
# cv2.namedWindow(window_name)
#
# while True:
#     resp = s.recv(1024)
#     if len(resp) == 0:
#         break
#
#     buffer += resp
#     response_1 = buffer.find(b'\xff\xd8')
#     response_2 = buffer.find(b'\xff\xd9')
#
#     if response_1 != -1 and response_2 != -1:
#         jpg = buffer[response_1:response_2 + 2]
#         buffer = buffer[response_2 + 2:]
#         image = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8), 1)
#
#         cv2.imshow(window_name, image)
#         key = cv2.waitKey(1)
#         if key != 255:
#             break
#
# # Close the connection when completed
# s.close()
