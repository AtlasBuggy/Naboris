import re
import asyncio

from atlasbuggy.log import PlaybackNode

from .actuators import Bno055Message, EncoderMessage


class ActuatorsPlayback(PlaybackNode):
    def __init__(self, file_name, directory=None, enabled=True):
        super(ActuatorsPlayback, self).__init__(file_name, directory=directory, enabled=enabled)

        self.num_leds = None
        self.temperature = None

        self.led_states = None
        self.turret_yaw = 90
        self.turret_azimuth = 90

        self.commanded_speed = 0
        self.commanded_angle = 0
        self.commanded_angular = 0

        self.right_tick = 0
        self.left_tick = 0
        self.right_updated = True
        self.left_updated = True

        self.encoder_message = None
        self.encoder_service = "encoder"
        self.define_service(self.encoder_service, message_type=EncoderMessage)

        self.print_bno055_output = False
        self.bno055_packet_header = "imu"
        self.bno055_service = "bno055"
        self.prev_bno_angle = 0.0
        self.delta_bno_angle = 0.0
        self.define_service(self.bno055_service, message_type=Bno055Message)

        # self.enc_times = []
        # self.enc_left_ticks = []
        # self.enc_right_ticks = []
        # self.bno_times = []
        # self.bno_angles = []

        self.motor_command_regex = r"speed=(-?[0-9]\d*), angle=(-?[0-9]\d*), angular=(-?[0-9]\d*)"

    async def parse(self, line):
        message = Bno055Message.parse(line.message)
        if message is not None:
            await self.broadcast(message, self.bno055_service)
            # self.bno_times.append(message.timestamp)
            # self.bno_angles.append(message.euler.z)

            self.delta_bno_angle = message.euler.z - self.prev_bno_angle
            return

        message = EncoderMessage.parse(line.message)
        if message is not None:
            message.compute_deltas(self.encoder_message, self.commanded_angle)

            self.encoder_message = message
            # self.enc_times.append(message.packet_time)
            # self.enc_left_ticks.append(message.left_tick)
            # self.enc_right_ticks.append(message.right_tick)

            await self.broadcast(message, self.encoder_service)
            return

        match = re.match(self.motor_command_regex, line.message)
        if match is not None:
            self.commanded_speed = int(match.group(1))
            self.commanded_angle = (180 - int(match.group(2))) % 360
            self.commanded_angular = int(match.group(3))

        self.logger.info(line.full)
        await asyncio.sleep(0.0)

        # async def teardown(self):
        #     with open("enc_data.txt", 'w') as file:
        #         for enc_time, right_tick, left_tick in zip(self.enc_times, self.enc_right_ticks, self.enc_left_ticks):
        #             file.write("%s\t%s\t%s\n" % (enc_time, right_tick, left_tick))
        #
        #     with open("bno_data.txt", 'w') as file:
        #         for bno_time, angle in zip(self.bno_times, self.bno_angles):
        #             file.write("%s\t%s\n" % (bno_time, angle))
