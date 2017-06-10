import serial
import time
import numpy as np
from threading import Lock
from serial.serialutil import SerialException
from atlasbuggy.datastream import ThreadedStream


class LMS200(ThreadedStream):
    def __init__(self, port, enabled=True, log_level=None, baud=9600, is_live=True):
        super(LMS200, self).__init__(enabled, log_level=log_level)

        self.port_address = port
        self.baud_rate = baud
        self.serial_ref_timeout = 1.0
        self.serial_ref = None
        self.serial_lock = Lock()
        self.buffer = b''
        self.recording_buffer = ""

        self.point_cloud = None
        self.units = "mm"
        self.is_complete_scan = True
        self.resolution = 0.5
        self.distances = []
        self.angles = np.array([])

        self.simulated_contents = b''
        self.simulated_index = 0

        self.is_live = is_live

        self.valid_bauds = 9600, 19200, 38400

    def open_port(self):
        if self.is_live:
            error = None
            try:
                self.serial_ref = serial.Serial(
                    port=self.port_address,
                    baudrate=self.baud_rate,
                    timeout=self.serial_ref_timeout
                )
                self.logger.info("opened serial")
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

    def write_telegram(self, address, packet, skip_check=True):
        telegram = self.generate_telegram(address, packet)
        if self.is_live and self.serial_ref is not None:
            self.serial_ref.flush()
            self.logger.info("Writing %s" % telegram)
            self.serial_ref.write(telegram)

            if not skip_check:
                while True:
                    with self.serial_lock:
                        ack = self.serial_ref.read(1)
                    self.logger.info(ack)
                    if len(ack) > 0:
                        if ack == b'\x06':
                            return True
                        elif ack == b'\x15':
                            return False
                        else:
                            self.logger.warning("Invalid value received (neither ACK, nor NACK): " + repr(ack))
                            return None
        else:
            self.logger.info("writing:", telegram)

    def set_simulated_data(self, contents):
        self.simulated_index = 0
        self.simulated_contents = contents
        self.check_serial()

    def write_reset(self):
        self.write_telegram(0, b'\x10')

    def write_start_measuring(self):
        self.write_telegram(0, b'\x20\x20', skip_check=False)
        self.logger.info("Wrote start")

    def write_installation_mode(self):
        self.write_telegram(0, b'\x20\x00SICK_LMS')

    def change_baud(self, new_baud):
        if self.serial_ref is not None and self.serial_ref.isOpen():
            if new_baud not in self.valid_bauds:
                raise ValueError("Invalid input baud rate: %s. Valid rates are: %s" % (new_baud, self.valid_bauds))

            baud_command = None
            if new_baud == self.valid_bauds[0]:
                baud_command = b'\x42'
            elif new_baud == self.valid_bauds[1]:
                baud_command = b'\x41'
            elif new_baud == self.valid_bauds[2]:
                baud_command = b'\x40'

            if baud_command is not None:
                self.write_telegram(0, b'\x20' + baud_command)
                self.logger.info("Changing baud to: %s" % new_baud)
                with self.serial_lock:
                    self.serial_ref.baudrate = new_baud

    def request_status(self):
        self.write_telegram(0, b'\x31')

    # TODO: understand all important commands and write them
    # standby mode
    # change baud
    # change resolution
    # change range
    # change sample speed

    def start(self):
        self.open_port()
        # self.write_start_measuring()
        # self.change_baud(38400)
        # time.sleep(0.05)
        # self.request_status()
        # self.write_reset()

    def run(self):
        self.logger.info("Reading serial port '%s'..." % self.port_address)

        while self.running():
            self.check_serial()

    def check_serial(self):
        self.buffer = b''
        # if self.should_log:
        #     self.recording_buffer = ""
        if self.read(1) == b'\x02':
            if self.read(1) == b'\x80':
                length = self.parse_16bit(ord(self.read(1)), ord(self.read(1)))
                payload = self.read(length)
                response = payload[0]
                data = payload[1:]
                checksum = self.parse_16bit(ord(self.read(1)), ord(self.read(1)))
                calc_checksum = self.lms200_crc(self.buffer[:-2])
                if calc_checksum != checksum:
                    self.logger.warning("!!invalid checksum!! found: %s != calculated: %s, %s" % (
                        checksum, calc_checksum, repr(self.buffer)), ignore_flag=True)
                    return

                if response == 0xA0:
                    self.logger.info("mode switched")
                elif response == 0x90:
                    self.logger.info("powered on", data)
                elif response == 0xB0:
                    # self.logger.info("got measurement")
                    self.parse_measurements(data)
                else:
                    self.logger.info("%s, %s" % (response, data))
                    # TODO: add more responses

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
        self.angles = np.linspace(0, np.pi, int(num_samples) - 1)
        for sample_index in range(2, num_samples * 2, 2):
            self.distances.append(self.parse_16bit(data[sample_index], data[sample_index + 1]))

        self.distances = np.array(self.distances)
        self.point_cloud = np.vstack([self.distances * np.cos(self.angles), self.distances * np.sin(self.angles)]).T
        self.point_cloud_received(self.point_cloud)

    def point_cloud_received(self, point_cloud):
        pass

    def read(self, n):
        result = b'\x00'
        if self.is_live:
            if self.serial_ref.isOpen():
                with self.serial_lock:
                    result = self.serial_ref.read(n)
        else:
            result = self.simulated_contents[self.simulated_index: self.simulated_index + n]
            self.simulated_index += n
        self.buffer += result

        # if self.should_log:
        #     self.recording_buffer += ("%02x " * len(result)) % tuple([b for b in result])
        return result

    def close(self):
        # TODO: find better closing behavior (don't just write reset every time)
        if self.is_live:
            if self.serial_ref is not None:
                # self.write_reset()
                with self.serial_lock:
                    self.serial_ref.close()
                    self.logger.info("serial closed")
