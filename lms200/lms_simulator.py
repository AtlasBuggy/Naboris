import asyncio
from atlasbuggy.logparser import LogParser
from atlasbuggy.robot import Robot
from mylms import MyLMS


class Simulator(LogParser):
    def __init__(self, file_name, directory="", enabled=True, log_level=None):
        super(Simulator, self).__init__(file_name, directory, enabled, log_level=log_level)
        self.lms_parser = None

    def take(self):
        self.lms_parser = self.streams["lms_parser"]
        self.lms_parser.initialized()

    async def update(self):
        await asyncio.sleep(0.0)

    def stop(self):
        self.lms_parser.stop()

robot = Robot()

lms200 = MyLMS(make_image=False)
simulator = Simulator("logs/2017_Jun_15/11;00;13.log.xz")

simulator.give(lms_parser=lms200)

robot.run(simulator, lms200.plotter)
