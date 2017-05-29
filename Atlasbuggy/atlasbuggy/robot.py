import time
import asyncio
from atlasbuggy.datastream import DataStream


class Robot:
    def __init__(self, *streams, setup_fn=None, loop_fn=None):
        """
        :param robot_objects: instances of atlasbuggy.robot.object.RobotObject or
            atlasbuggy.robot.object.RobotObjectCollection
        """

        self.streams = []
        self.loop_fn = loop_fn
        self.setup_fn = setup_fn
        for stream in streams:
            if stream.enabled:
                self.streams.append(stream)
        self.loop = asyncio.get_event_loop()

    @staticmethod
    def run(*streams, setup_fn=None, loop_fn=None):
        Robot(*streams, setup_fn=setup_fn, loop_fn=loop_fn)._run()

    def _run(self):
        """
        Events to be run when the interface starts (receive_first has been for all enabled robot objects)
        :return: None if ok, "error", "exit", or "done" if the program should exit
        """
        tasks = []
        for stream in self.streams:
            stream.asyncio_loop = self.loop
            if not stream.threaded and stream.asynchronous:
                task = stream.run()
                tasks.append(task)
                stream.task = task

        if self.loop_fn is not None:
            tasks.append(self.loop_fn(self))

        coroutine = asyncio.gather(*tasks)
        for stream in self.streams:
            stream.coroutine = coroutine

        try:
            for stream in self.streams:
                stream.stream_start()

            if self.setup_fn is not None:
                self.setup_fn(self)

            self.loop.run_until_complete(coroutine)
            while DataStream.all_running():
                time.sleep(0.1)  # in case there are no async functions to run
        except KeyboardInterrupt:
            coroutine.cancel()
        except asyncio.CancelledError:
            pass
        finally:
            DataStream.all_exited.set()
            for stream in self.streams:
                stream.stream_close()
            self.loop.close()
