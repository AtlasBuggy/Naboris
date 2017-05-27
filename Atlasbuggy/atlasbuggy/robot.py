import asyncio


class Robot:
    def __init__(self, *streams):
        """
        :param robot_objects: instances of atlasbuggy.robot.object.RobotObject or
            atlasbuggy.robot.object.RobotObjectCollection
        """

        self.streams = []
        for stream in streams:
            if stream.enabled:
                self.streams.append(stream)
        self.loop = asyncio.get_event_loop()

    def run(self):
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

        coroutine = asyncio.gather(*tasks)
        for stream in self.streams:
            stream.coroutine = coroutine

        try:
            for stream in self.streams:
                stream.stream_start()

            self.loop.run_until_complete(coroutine)
        except KeyboardInterrupt:
            coroutine.cancel()
        except asyncio.CancelledError:
            pass
        finally:
            for stream in self.streams:
                stream.stream_close()
            self.loop.close()
