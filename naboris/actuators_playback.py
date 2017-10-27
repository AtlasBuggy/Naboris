import asyncio

from atlasbuggy.log import PlaybackNode

from .actuators import Bno055Message


class ActuatorsPlayback(PlaybackNode):
    def __init__(self, file_name, directory=None, enabled=True):
        super(ActuatorsPlayback, self).__init__(file_name, directory=directory, enabled=enabled)

    async def parse(self, line):
        message = Bno055Message.parse(line.message)
        if message is not None:
            print(message.euler.get_tuple())
            await self.broadcast(message)
        else:
            self.logger.info(line.full)
            await asyncio.sleep(0.0)
