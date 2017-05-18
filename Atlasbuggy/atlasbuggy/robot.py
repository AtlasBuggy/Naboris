import asyncio


class Robot:
    def __init__(self, *streams):
        """
        :param robot_objects: instances of atlasbuggy.robot.object.RobotObject or
            atlasbuggy.robot.object.RobotObjectCollection
        """

        self.streams = {}
        for stream in streams:
            self.streams[stream.name] = stream
        self.loop = asyncio.get_event_loop()

    def run(self):
        """
        Events to be run when the interface starts (receive_first has been for all enabled robot objects)
        :return: None if ok, "error", "exit", or "done" if the program should exit
        """
        for stream in self.streams.values():
            stream.asyncio_loop = self.loop
            stream.streams = self.streams
            stream.start()

        try:
            tasks = asyncio.gather(*[stream.run() for stream in self.streams.values()])
            self.loop.run_until_complete(tasks)
        except KeyboardInterrupt:
            tasks.cancel()
        except asyncio.CancelledError:
            pass
        finally:
            for stream in self.streams.values():
                stream.close()
            self.loop.close()
