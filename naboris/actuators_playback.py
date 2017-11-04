import asyncio

from atlasbuggy.log import PlaybackNode

from .actuators import Bno055Message


class ActuatorsPlayback(PlaybackNode):
    def __init__(self, file_name, directory=None, enabled=True):
        super(ActuatorsPlayback, self).__init__(file_name, directory=directory, enabled=enabled)

        self.vx = 0.0
        self.vy = 0.0
        self.vz = 0.0
        self.prev_t = None

    async def parse(self, line):
        message = Bno055Message.parse(line.message)
        if message is not None:
            # print(("%0.4f\t" * 3) % message.linaccel.get_tuple())

            if self.prev_t is not None:
                dt = message.timestamp - self.prev_t
                self.vx += message.linaccel.x * dt
                self.vy += message.linaccel.y * dt
                self.vz += message.linaccel.z * dt

                print(("%0.4f\t" * 3) % (self.vx, self.vy, self.vz))

            self.prev_t = message.timestamp

            await self.broadcast(message)
        else:
            self.logger.info(line.full)
            await asyncio.sleep(0.0)
