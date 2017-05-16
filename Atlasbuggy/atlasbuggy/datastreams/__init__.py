import time
from threading import Event


class DataStream:
    def __init__(self, stream_name, log, debug):
        self.name = stream_name
        self.log = log
        self.debug = debug

        self.timestamp = None
        self.packet = ""

        self.start_time = 0.0

        self.started = Event()
        self.closed = Event()

    def start(self):
        if not self.started.is_set():
            self.started.set()
            self.start_time = time.time()
            return self.stream_start()

    def stream_start(self):
        pass

    def stream_update(self):
        pass

    def debug_print(self, *values, ignore_flag=False):
        string = "[%s] %s" % (self.name, " ".join([str(x) for x in values]))

        self.record(self.timestamp, self.name, string, "debug")

        if self.debug or ignore_flag:
            print(string)

    def handle_error(self, error, traceback):
        """
        Format the thrown error for logging. Return it after
        :param error: Error being thrown
        :param traceback: stack trace of error
        :return: Error being thrown
        """
        self.stream_handle_error()

        if self.log:
            error_message = "".join(traceback[:-1])
            error_message += "%s: %s" % (error.__class__.__name__, error.args[0])
            error_message += "\n".join(error.args[1:])
            self.record(self.timestamp, error.__class__.__name__, error_message, "error")

        # close log
        self.debug_print("logger closed")
        return error

    def stream_handle_error(self):
        pass

    def close(self):
        if not self.closed.is_set():
            self.closed.set()
            self.stream_close()
            # close log

    def stream_close(self):
        pass

    def record(self, timestamp, whoiam, packet, packet_type):
        pass
