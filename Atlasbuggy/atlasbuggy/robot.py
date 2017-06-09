import os
import time
import logging
import asyncio
from atlasbuggy.datastream import DataStream, AsyncStream


class Robot:
    def __init__(self, *streams, setup_fn=None, loop_fn=None, close_fn=None):
        self.streams = []

        self.loop_fn = loop_fn
        self.setup_fn = setup_fn
        self.close_fn = close_fn

        self.log_info = dict(
            file_name=time.strftime("%H;%M;%S.log"),
            directory=time.strftime("logs/%Y_%b_%d"),
            write=False,
            level=logging.DEBUG,
            format="[%(name)s @ %(filename)s:%(lineno)d][%(levelname)s] %(asctime)s: '%(message)s'",
            print_handle=None,
            file_handle=None
        )

        for stream in streams:
            if stream.enabled:
                self.streams.append(stream)
                stream.log_info = self.log_info
        self.loop = asyncio.get_event_loop()

    def init_logger(self, **kwargs):
        self.log_info.update(kwargs)

        if self.log_info["write"] and not os.path.isdir(self.log_info["directory"]):
            os.makedirs(self.log_info["directory"])

        # create console handler and set level to info
        self.log_info["print_handle"] = logging.StreamHandler()
        self.log_info["print_handle"].setLevel(self.log_info["level"])
        formatter = logging.Formatter(self.log_info["format"])
        self.log_info["print_handle"].setFormatter(formatter)

        if self.log_info["write"]:
            # create debug file handler and set level to debug
            self.log_info["file_handle"] = logging.FileHandler(
                os.path.join(self.log_info["directory"], self.log_info["file_name"]), "w+")
            self.log_info["file_handle"].setLevel(logging.INFO)
            formatter = logging.Formatter(self.log_info["format"])
            self.log_info["file_handle"].setFormatter(formatter)

    def run(self):
        coroutine = None
        try:
            for stream in self.streams:
                stream._start()

            if self.setup_fn is not None:
                self.setup_fn(self)

            coroutine = self.get_coroutine()
            self.loop.run_until_complete(coroutine)

        except KeyboardInterrupt:
            if coroutine is not None:
                coroutine.cancel()
        except asyncio.CancelledError:
            pass
        finally:
            if self.close_fn is not None:
                self.close_fn(self)
            self.exit_all()
            for stream in self.streams:
                stream._close()
            self.loop.close()

    def get_coroutine(self):
        tasks = []
        for stream in self.streams:
            if not isinstance(stream, DataStream):
                raise RuntimeError("Found an object that isn't a stream!", repr(stream))
            if isinstance(stream, AsyncStream):
                stream.asyncio_loop = self.loop
                task = stream.run()
                tasks.append(task)
                stream.task = task

        if self.loop_fn is not None:
            tasks.append(self.loop_fn(self))

        coroutine = asyncio.gather(*tasks)
        for stream in self.streams:
            stream.coroutine = coroutine

        return coroutine

    @staticmethod
    def exit_all():
        DataStream.exit_all()
