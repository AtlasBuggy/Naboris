import cv2
import numpy as np
import multiprocessing
from multiprocessing import Process, Lock, Queue, Event, Value
from atlasbuggy.datastream import DataStream


class CvPipeline(DataStream):
    def __init__(self, capture, enabled, debug, frames_are_arrays, processes=None):
        super(CvPipeline, self).__init__(enabled, debug, True, False)

        self.frames_are_arrays = frames_are_arrays
        self._output_raw_frames = Value('i', False)
        self.frame = None
        self.capture = capture

        self.input_lock = Lock()
        self.input_frames = Queue()

        self.output_lock = Lock()
        self.output_queue = Queue()

        self.raw_frame_lock = Lock()
        self.raw_frame_queue = Queue()

        self.should_exit = Event()

        if processes is None:
            self.process_count = multiprocessing.cpu_count() - 1
        else:
            self.process_count = processes

        self.debug_print("Using %s processes" % self.process_count)

        self.process = Process(target=self.process_frames)

    def output_raw_frames(self, value):
        # with self._output_raw_frames.get_lock():
            self._output_raw_frames.value = int(value)

    def start(self):
        self.process.start()

    def run(self):
        while self.are_others_running():
            if self.capture.frame is not None:
                if self.frames_are_arrays:
                    self.put(np.copy(self.capture.frame))
                else:
                    self.put(self.capture.frame.copy())

        self.should_exit.set()

    def get(self):
        with self.output_lock:
            if self.output_queue.empty():
                output = None
            else:
                output = self.output_queue.get()
        if output is None:
            self.frame = None
        else:
            self.frame = output[0]
        return output

    def get_raw(self):
        with self.raw_frame_lock:
            if self.raw_frame_queue.empty():
                raw_frame = None
            else:
                raw_frame = self.raw_frame_queue.get()
        return raw_frame

    def put(self, frame):
        with self.input_lock:
            self.input_frames.put(frame)

    def process_frames(self):
        error = None
        try:
            while not self.should_exit.is_set():
                with self.input_lock:
                    if self.input_frames.empty():
                        continue
                    else:
                        frame = self.input_frames.get()

                output, raw_frame = self._pipeline(frame)

                with self.output_lock:
                    self.output_queue.put(output)

                with self.raw_frame_lock:
                    if raw_frame is not None:
                        self.raw_frame_queue.put(raw_frame)
        except BaseException as _error:
            error = _error
            self.exit()
        if error is not None:
            raise error

    def _pipeline(self, frame):
        if not self.frames_are_arrays:
            frame = self.bytes_to_numpy(frame)

        output = self.pipeline(frame)
        # with self._output_raw_frames.get_lock():
        if self._output_raw_frames.value:
            return output, self.numpy_to_bytes(frame)
        else:
            return output, None

    @staticmethod
    def bytes_to_numpy(frame):
        return cv2.imdecode(np.fromstring(frame, dtype=np.uint8), 1)

    @staticmethod
    def numpy_to_bytes(frame):
        return cv2.imencode(".jpg", frame)[1].tostring()

    def pipeline(self, frame):
        raise NotImplementedError("Please override this method.")
