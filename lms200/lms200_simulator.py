import asyncio
from atlasbuggy.robot import Robot
from atlasbuggy.files.parser import Parser
from mylms import MyLMS, plotter


class LMSparser(Parser):
    def __init__(self):
        self.lms200 = MyLMS(False)
        super(LMSparser, self).__init__("23;49", "2017_Jun_08")

    async def update(self):
        await asyncio.sleep(0.03)

    def receive_user(self, whoiam, timestamp, packet):
        packet_bytes = b''
        for element in packet.split(" "):
            if len(element) > 0:
                packet_bytes += bytes([int(element, 16)])
        self.lms200.set_simulated_data(packet_bytes)


Robot.run(LMSparser(), plotter)
