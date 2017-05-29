import cv2
import numpy as np
from queue import Queue
from atlasbuggy.datastream import DataStream


class CvPipeline(DataStream):
    def __init__(self, capture, enabled, debug, name=None, generate_bytes=False):
        super(CvPipeline, self).__init__(enabled, debug, True, False, name)
        self.capture = capture

        self.frame = None
        self.bytes_frame = None

        self.generate_bytes = generate_bytes
        self.output_queue = Queue()

    def run(self):
        while self.all_running():
            if self.capture.frame is not None:
                self.frame = self.capture.get_frame()

                output = self.pipeline(self.frame)
                if type(output) != tuple:
                    self.frame = output
                else:
                    self.frame = output[0]
                    self.output_queue.put(output[1:])

                if self.generate_bytes:
                    self.bytes_frame = self.capture.numpy_to_bytes(self.frame)
            else:
                self.bytes_frame = None

    def get(self):
        while not self.output_queue.empty():
            yield self.output_queue.get()

    def pipeline(self, frame):
        raise NotImplementedError("Please override this method.")
