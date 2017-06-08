import time
import asyncio
from atlasbuggy.datastream import DataStream


class Robot:
    def __init__(self, *streams, setup_fn=None, loop_fn=None, close_fn=None, run_forever=False):
        """
        :param robot_objects: instances of atlasbuggy.robot.object.RobotObject or
            atlasbuggy.robot.object.RobotObjectCollection
        """

        self.streams = []

        self.loop_fn = loop_fn
        self.setup_fn = setup_fn
        self.close_fn = close_fn
        self.close_fn_called = False

        self.run_forever = run_forever

        for stream in streams:
            if stream.enabled:
                self.streams.append(stream)
        self.loop = asyncio.get_event_loop()

    @staticmethod
    def run(*streams, setup_fn=None, loop_fn=None, close_fn=None, run_forever=True):
        Robot(*streams, setup_fn=setup_fn, loop_fn=loop_fn, close_fn=close_fn)._run()

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

            if self.close_fn is not None:
                self.close_fn(self)
                self.close_fn_called = True

            if self.run_forever:
                self.loop.run_forever()
            else:
                while DataStream.all_running():
                    time.sleep(0.1)  # in case there are no async functions to run
        except KeyboardInterrupt:
            coroutine.cancel()
        except asyncio.CancelledError:
            pass
        finally:
            if self.close_fn is not None and not self.close_fn_called:
                self.close_fn(self)
                self.close_fn_called = True
            self.exit()
            for stream in self.streams:
                stream.stream_close()
            self.loop.close()

    def exit(self):
        DataStream.all_exited.set()
