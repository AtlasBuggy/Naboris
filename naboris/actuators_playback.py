import asyncio

from atlasbuggy.log import PlaybackNode

from .actuators import Bno055Message, EncoderMessage


class ActuatorsPlayback(PlaybackNode):
    def __init__(self, file_name, directory=None, enabled=True):
        super(ActuatorsPlayback, self).__init__(file_name, directory=directory, enabled=enabled)

        self.num_leds = None
        self.temperature = None
        self.ticks_to_mm = 1.0

        self.led_states = None
        self.turret_yaw = 90
        self.turret_azimuth = 90

        self.right_tick = 0
        self.left_tick = 0
        self.encoder_message = None
        self.encoder_service = "encoder"
        self.define_service(self.encoder_service, message_type=EncoderMessage)

        self.print_bno055_output = False
        self.bno055_packet_header = "imu"
        self.bno055_service = "bno055"
        self.define_service(self.bno055_service, message_type=Bno055Message)

    async def parse(self, line):
        message = Bno055Message.parse(line.message)
        if message is not None:
            await self.broadcast(message, self.bno055_service)
            return

        message = EncoderMessage.parse(line.message)
        if message is not None:
            message.prev_message = self.encoder_message
            self.encoder_message = message
            await self.broadcast(message, self.encoder_service)
            return

        self.logger.info(line.full)
        await asyncio.sleep(0.0)
