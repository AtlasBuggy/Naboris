import serial
import time
import numpy as np
from threading import Lock
from serial.serialutil import SerialException
from atlasbuggy.datastream import ThreadedStream


class LMS200(ThreadedStream):
    lms_default_baud = 9600

    def __init__(self, port, enabled=True, log_level=None, baud=9600, is_live=True):
        super(LMS200, self).__init__(enabled, log_level=log_level)

        self.port_address = port
        self.baud_rate = baud
        self.serial_ref_timeout = 1
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

        self.measuring_modes = {
            "default"                  : b'\x00',
            "8m/80m; fields A,B,Dazzle": b'\x00',
            "8m/80m; 3 reflector bits" : b'\x01',
            "8m/80m; fields A,B,C"     : b'\x02',
            "16m; 4 reflector bits"    : b'\x03',
            "16m; fields A & B"        : b'\x04',
            "32m; 2 reflector bits"    : b'\x05',
            "32m; field A"             : b'\x06',
            "32m; immediate"           : b'\x0f',
            "Reflectivity"             : b'\x3f',
        }
        self.measuring_mode = self.measuring_modes["default"]

    def open_port(self):
        if self.is_live:
            error = None
            try:
                self.serial_ref = serial.Serial(
                    port=self.port_address,
                    baudrate=self.baud_rate,
                    timeout=self.serial_ref_timeout
                )
                self.logger.debug("opened serial")
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

    def write_telegram(self, address, packet, skip_check=False):
        telegram = self.generate_telegram(address, packet)
        self.logger.debug("[writing] %s" % telegram)
        if self.is_live and self.serial_ref is not None:
            self.serial_ref.flush()
            self.serial_ref.write(telegram)

            if not skip_check:
                self.check_for_ack()

    def check_for_ack(self):
        t0 = time.time()
        while True:
            with self.serial_lock:
                ack = self.serial_ref.read(1)
            self.logger.debug("command response: %s" % ack)

            if len(ack) > 0:
                if ack == b'\x06':
                    return True
                elif ack == b'\x15':
                    return False
                else:
                    self.logger.warning("Invalid value received (neither ACK, nor NACK): " + repr(ack))
                    return None
            elif (time.time() - t0) > 3:
                self.logger.warning("timeout!")
                self.exit_all()
                return None

    def reset(self):
        self.logger.debug("[command] Writing reset")
        self.write_telegram(0, b'\x10')

    def start_measuring(self):
        self.logger.debug("[command] Writing start")
        self.write_telegram(0, b'\x20\x24')

    def set_to_request_mode(self):
        self.logger.debug("[command] setting to standby")
        self.write_telegram(0, b'\x20\x25', skip_check=True)

    def set_measuring_mode(self, mode):
        self.logger.debug("[command] measurement mode to %s" % mode)
        if self.measuring_modes[mode] != self.measuring_mode:
            self.measuring_mode = self.measuring_modes[mode]
            # see page 31 of LMS200 telegram listing for full config telegram
            self.write_telegram(
                # b'\x00\x00\x70\x00\x00\x00\x01\x00\x00\x02\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00'
                0, b'\x77\x00\x00\x70\x00\x00\x00' + self.measuring_mode + b'\x00\x00\x02\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00'
            )

    def change_baud(self, new_baud):
        if self.serial_ref is not None and self.serial_ref.isOpen():
            if new_baud not in self.valid_bauds:
                raise ValueError(
                    "Invalid input baud rate: %s. Valid rates are: %s" % (new_baud, self.valid_bauds))

            baud_command = None
            if new_baud == self.valid_bauds[0]:  # 9600
                baud_command = b'\x42'
            elif new_baud == self.valid_bauds[1]:  # 19200
                baud_command = b'\x41'
            elif new_baud == self.valid_bauds[2]:  # 38400
                baud_command = b'\x40'

            if baud_command is not None:
                self.logger.debug("[command] Changing baud to: %s" % new_baud)
                self.write_telegram(0, b'\x20' + baud_command, skip_check=True)
                with self.serial_lock:
                    self.serial_ref.baudrate = new_baud
                self.baud_rate = new_baud

                time.sleep(0.25)

                # self.check_for_ack()

    # TODO: understand all important commands and write them
    # standby mode
    # change resolution
    # change range
    # change sample speed

    def start(self):
        self.logger.debug("Reading serial port '%s'..." % self.port_address)
        self.open_port()
        # self.change_baud(self.valid_bauds[2])
        # self.set_measuring_mode("32m; immediate")
        self.start_measuring()

    def run(self):
        while self.running():
            self.buffer = b''
            self.recording_buffer = ""
            if self.read(1) == b'\x02':
                if self.read(1) == b'\x80':
                    length, status = self.read_16_bit()
                    if not status:
                        break

                    payload = self.read(length)
                    response = payload[0]
                    data = payload[1:]

                    checksum, status = self.read_16_bit()
                    if not status:
                        break

                    calc_checksum = self.lms200_crc(self.buffer[:-2])
                    if calc_checksum != checksum:
                        self.logger.warning("!!invalid checksum!! found: %s != calculated: %s, %s" % (
                            checksum, calc_checksum, repr(self.buffer)))
                        break

                    if response == 0xA0:
                        self.logger.debug("mode switched: %s" % data)
                    elif response == 0x90:
                        self.logger.debug("powered on", data)
                    elif response == 0xB0:
                        self.parse_measurements(data)
                    else:
                        self.logger.debug("%s, %s" % (response, data))
                        # TODO: add more responses

                    self.logger.debug("[buffer] <%s>" % self.recording_buffer)

        self.logger.debug("stopped running")
        if self.serial_ref is not None:
            self.set_to_request_mode()
            # self.set_measuring_mode("default")
            if self.baud_rate != self.lms_default_baud:
                self.change_baud(self.lms_default_baud)

            self.serial_ref.stop()

    def read_16_bit(self):
        lower_byte = self.read(1)
        upper_byte = self.read(1)
        if len(upper_byte) == 0 or len(lower_byte) == 0:
            self.logger.debug("No bytes found!")
            return 0, False

        upper_byte = ord(upper_byte)
        lower_byte = ord(lower_byte)
        value = (upper_byte << 8) + lower_byte
        return value, True

    def parse_measurements(self, data):
        sample_info = (data[1] << 8) + data[0]
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
            sample = (data[sample_index + 1] << 8) + data[sample_index]
            self.distances.append(sample)

        self.distances = np.array(self.distances)
        self.point_cloud = np.vstack(
            [self.distances * np.cos(self.angles), self.distances * np.sin(self.angles)]).T
        self.point_cloud_received(self.point_cloud)

    def point_cloud_received(self, point_cloud):
        pass

    def read(self, n):
        result = b''
        if self.is_live:
            with self.serial_lock:
                if self.serial_ref.isOpen() and self.running():
                    result = self.serial_ref.read(n)
        else:
            result = self.simulated_contents[self.simulated_index: self.simulated_index + n]
            self.simulated_index += n
        self.buffer += result

        self.recording_buffer += ("%02x" * len(result)) % tuple([b for b in result])
        return result

    # def close(self):

