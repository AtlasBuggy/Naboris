import serial
import time
import numpy as np
from threading import Lock
from serial.serialutil import SerialException
from atlasbuggy.datastream import DataStream


class LMS200(DataStream):
    def __init__(self, port, enabled=True, debug=False, baud=9600, is_live=True, logger=None):
        super(LMS200, self).__init__(enabled, debug, True, False)

        self.port_address = port
        self.baud_rate = baud
        self.serial_ref_timeout = 1.0
        self.serial_ref = None
        self.read_lock = Lock()
        self.buffer = b''

        self.point_cloud = None
        self.units = "mm"
        self.is_complete_scan = True
        self.resolution = 0.5
        self.distances = []
        self.angles = np.array([])

        self.simulated_contents = b''
        self.simulated_index = 0

        self.is_live = is_live
        self.logger = logger
        self.should_log = self.logger is not None and self.logger.enabled and self.is_live

    def open_port(self):
        if self.is_live:
            error = None
            try:
                self.serial_ref = serial.Serial(
                    port=self.port_address,
                    baudrate=self.baud_rate,
                    timeout=self.serial_ref_timeout
                )
            except SerialException as _error:
                self.exit()
                error = _error

            if error is not None:
                raise error

    def generate_telegram(self, address, payload):
        data = b'\x02' + chr(address).encode()
        length = len(payload)
        data += chr(length & 0xFF).encode()
        data += chr((length >> 8) & 0xFF).encode()
        data += payload
        crc = self.lms200_crc(data)
        data += chr(crc & 0xFF).encode()
        data += chr((crc >> 8) & 0xFF).encode()
        return data

    @staticmethod
    def lms200_crc(data):
        crc16 = 0
        byte = [0, 0]
        for c in data:
            byte[1] = byte[0]
            byte[0] = c

            if crc16 & 0x8000:
                crc16 = (crc16 & 0x7FFF) << 1
                crc16 ^= 0x8005
            else:
                crc16 = crc16 << 1

            crc16 ^= (byte[1] << 8) | byte[0]

        return crc16

    @staticmethod
    def parse_16bit(lower_byte, upper_byte):
        return (upper_byte << 8) + lower_byte

    def write_telegram(self, address, packet):
        telegram = self.generate_telegram(address, packet)
        if self.is_live and self.serial_ref is not None:
            self.serial_ref.flush()
            self.serial_ref.write(telegram)

            while True:
                ack = self.serial_ref.read(1)
                if len(ack) > 0:
                    if ack == b'\x06':
                        return True
                    elif ack == b'\x15':
                        return False
                    else:
                        self.debug_print("Invalid value received (neither ACK, nor NACK)", repr(ack))
        else:
            self.debug_print("writing:", telegram)

    def append_simulated_data(self, contents):
        self.simulated_contents += contents

    def write_reset(self):
        self.write_telegram(0, b'\x10')

    def write_start_measuring(self):
        self.write_telegram(0, b'\x20\x20')

    def write_installation_mode(self):
        self.write_telegram(0, b'\x20\x00SICK_LMS')

    # TODO: understand all important commands and write them
    # standby mode
    # change baud
    # change resolution
    # change range

    def start(self):
        self.open_port()
        self.write_start_measuring()

    def run(self):
        print("Reading serial port '%s'..." % self.port_address)

        while self.all_running():
            self.buffer = b''

            if self.read(1) == b'\x02':
                if self.read(1) == b'\x80':
                    length = self.parse_16bit(ord(self.read(1)), ord(self.read(1)))
                    payload = self.read(length)
                    response = payload[0]
                    data = payload[1:]
                    checksum = self.parse_16bit(ord(self.read(1)), ord(self.read(1)))
                    calc_checksum = self.lms200_crc(self.buffer[:-2])
                    if calc_checksum != checksum:
                        self.debug_print("!!invalid checksum!! found: %s != calculated: %s, '%s'" % (
                            checksum, calc_checksum, repr(self.buffer)), ignore_flag=True)
                        continue

                    if response == 0xA0:
                        print("mode switched")
                    elif response == 0x90:
                        print("powered on")
                    elif response == 0xB0:
                        self.parse_measurements(data)
                    # TODO: add more responses

                    if self.should_log:
                        self.logger.record(time.time(), self.name, str(self.buffer)[2:-1], "user")
        self.exit()

    def parse_measurements(self, data):
        sample_info = self.parse_16bit(data[0], data[1])
        num_samples = sample_info & 0x3ff

        unit_info_1 = sample_info >> 14 & 1
        unit_info_2 = sample_info >> 15 & 1
        if not unit_info_1 and not unit_info_2:
            self.units = "cm"
        elif unit_info_1 and not unit_info_2:
            self.units = "mm"
        else:
            self.units = "Reserved"

        scan_info = sample_info >> 13 & 1
        self.is_complete_scan = not bool(scan_info)

        resolution_info_1 = sample_info >> 11 & 1
        resolution_info_2 = sample_info >> 12 & 1

        if not resolution_info_1 and not resolution_info_2:
            self.resolution = 0
        elif resolution_info_1 and not resolution_info_2:
            self.resolution = 0.25
        elif not resolution_info_1 and resolution_info_2:
            self.resolution = 0.5
        else:
            self.resolution = 0.75

        self.distances = []
        self.angles = np.linspace(0, np.pi, int(num_samples / 2))
        for sample_index in range(0, num_samples, 2):
            self.distances.append(self.parse_16bit(data[sample_index], data[sample_index + 1]))

        self.distances = np.array(self.distances)

        self.point_cloud = np.vstack([self.distances * np.cos(self.angles), self.distances * np.sin(self.angles)]).T
        self.point_cloud_received(self.point_cloud)

    def point_cloud_received(self, point_cloud):
        pass

    def read(self, n):
        if self.is_live:
            with self.read_lock:
                result = self.serial_ref.read(n)
        else:
            result = self.simulated_contents[self.simulated_index: self.simulated_index + n]
            self.simulated_index += n
        if len(result) == 0:
            result = b'\x00'
        self.buffer += result
        return result

    def close(self):
        # TODO: find better closing behavior (don't just write reset every time)
        if self.is_live:
            with self.read_lock:
                self.write_reset()
            if self.serial_ref is not None:
                self.serial_ref.close()
        else:
            self.write_reset()
