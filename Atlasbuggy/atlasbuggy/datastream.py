import time
import asyncio
from threading import Event


class DataStream:
    def __init__(self, stream_name, debug):
        self.name = stream_name
        self.debug = debug

        self.timestamp = None
        self.packet = ""

        self.start_time = 0.0

        self.started = Event()
        self.closed = Event()

        self.streams = None
        self.tasks = None
        self.asyncio_loop = None

    def start(self):
        pass

    def stream_start(self):
        if not self.started.is_set():
            self.started.set()
            self.start_time = time.time()
            return self.start()

    def run(self):
        pass

    def debug_print(self, *values, ignore_flag=False):
        string = "[%s] %s" % (self.name, " ".join([str(x) for x in values]))

        self.stream_debug_print(string)

        if self.debug or ignore_flag:
            print(string)

    def stream_debug_print(self, string):
        pass

    def close(self):
        pass

    def stream_close(self):
        if not self.closed.is_set():
            self.closed.set()
            self.close()

    def exit(self):
        for task in asyncio.Task.all_tasks():
            task.cancel()
