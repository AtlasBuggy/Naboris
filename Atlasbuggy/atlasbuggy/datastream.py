import time
import asyncio
from threading import Thread, Event


class DataStream:
    def __init__(self, stream_name, enabled, debug, threaded, asynchronous):
        self.name = stream_name
        self.debug = debug
        self.enabled = enabled

        self.timestamp = None
        self.packet = ""

        self.start_time = 0.0

        self.started = Event()
        self.closed = Event()

        self.asynchronous = asynchronous
        self.asyncio_loop = None

        self.threaded = threaded
        if self.threaded:
            self.thread = Thread(target=self.run)
            self.thread.daemon = True
        else:
            self.thread = None

        # can't be threaded and asynchronous at the same time
        assert not (self.threaded and self.asynchronous)

    def start(self):
        pass

    def not_daemon(self):
        if self.threaded:
            self.thread.daemon = False

    def stream_start(self):
        if not self.enabled:
            return
        if not self.started.is_set():
            self.started.set()
            self.start_time = time.time()
            self.start()

            if self.threaded:
                self.thread.start()

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
        if not self.enabled:
            return
        if not self.closed.is_set():
            self.closed.set()
            self.close()

    def exit(self):
        for task in asyncio.Task.all_tasks():
            task.cancel()
