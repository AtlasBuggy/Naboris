from queue import Queue
from threading import Lock
from atlasbuggy.datastream import DataStream


class CvPipeline(DataStream):
    def __init__(self, capture, enabled, debug, name=None, generate_bytes=False, use_output_queue=False):
        super(CvPipeline, self).__init__(enabled, debug, True, False, name)
        self.capture = capture

        self.frame = None
        self.bytes_frame = None
        self.frame_lock = Lock()

        self.generate_bytes = generate_bytes
        self.output_queue = Queue()
        self.use_output_queue = use_output_queue

    def run(self):
        while self.all_running():
            if self.capture.frame is not None:
                output = self.pipeline(self.capture.get_frame())
                if type(output) != tuple:
                    self.frame = output
                else:
                    self.frame = output[0]
                    if self.use_output_queue:
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
