import time
import serial
import math
import numpy as np
from threading import Lock

from atlasbuggy.datastream import ThreadedStream

from sicklms.message import Message
from sicklms.constants import *
from sicklms.data_structures import *


class SickLMS(ThreadedStream):
    def __init__(self, port_address, baud=38400, enabled=True, name=None, log_level=None, dude_bro_mode=True,
                 mode=SICK_OP_MODE_MONITOR_STREAM_VALUES, mode_params=None):
        super(SickLMS, self).__init__(enabled, name, log_level)

        self.session_baud = baud
        if type(mode) == int and mode in sick_lms_operating_modes:
            self.session_mode = mode
        elif type(mode) == str and mode in sick_lms_operating_modes:
            self.session_mode = sick_lms_operating_modes[mode]
        else:
            self.session_mode = mode

        self.session_mode_params = mode_params

        self.device_path = port_address
        self.sick_type = SICK_LMS_TYPE_UNKNOWN
        self.operating_status = LmsOperatingStatus()
        self.config = LmsConfig()

        self.subrange_start_index = 0
        self.subrange_stop_index = 0
        self.mean_sample_size = 0

        self.current_scan = None
        self.b0_scan = ScanProfileB0()
        self.b6_scan = ScanProfileB6()
        self.b7_scan = ScanProfileB7()
        self.bf_scan = ScanProfileBF()
        self.c4_scan = ScanProfileC4()

        self.distances = np.array([])
        self.angles = np.array([])
        self.point_cloud = np.array([])

        self.serial_lock = Lock()
        self.serial_ref = None

        self.dude_bro_mode = dude_bro_mode

        self.recording_buffer = ""
        self.recv_message = Message()
        self.send_message = Message()

        if self.dude_bro_mode:
            self.logger.debug("SIIIIICK duuude... Welcome to the S I C K brooo")

    def start_up_commands(self):
        pass

    def _startup_lms(self):
        self._setup_connection()

        session_baud_set = False
        try:
            self._set_session_baud(self.session_baud)
            session_baud_set = True
        except (SickTimeoutException, SickIOException):
            if self.dude_bro_mode:
                self.logger.debug("Mah man looks to be we couldn't get that sweet baud you requested... "
                                  "We'll try one more time just for you bro")
            else:
                self.logger.debug("Failed to set requested baud rate. "
                                  "Attempting to detect LMS baud rate...")

        if not session_baud_set:
            discovered_baud = None
            for test_baud in sick_lms_baud_codes.keys():
                if self.dude_bro_mode:
                    self.logger.debug("Yooo we're tryin' this baud out dude: %s" % test_baud)

                if self._test_baud(test_baud):
                    discovered_baud = test_baud
                    break

            if discovered_baud is None:
                if self.dude_bro_mode:
                    raise SickIOException("Aww, bummer... maybe you'll get that sweet baud later bro...")
                else:
                    raise SickIOException("Failed to detect baud rate!")

            if self.dude_bro_mode:
                self.logger.debug("Tubular!! We're using this baud now dude: %s" % discovered_baud)
            else:
                self.logger.debug("Setting baud to: %s" % discovered_baud)
            self._set_session_baud(discovered_baud)

        self._get_type()
        self._get_status()
        self._get_config()

        self._switch_opmode(self.session_mode, self.session_mode_params)

    def run(self):
        # note to self: never have threads trying to access the same serial reference.
        # Keep all serial activities inside or outside the thread. Not both
        try:
            self._startup_lms()
            self.start_up_commands()
            self.logger.debug(self.status_string())

            while self.running():
                if self.operating_status.operating_mode == SICK_OP_MODE_MONITOR_STREAM_VALUES:
                    self.get_scan()
                    self._parse_point_cloud()
                    self.point_cloud_received(self.point_cloud)
                else:
                    time.sleep(0.05)
        except BaseException:
            self._teardown()
            raise
        try:
            self._teardown()
        except SickIOException:
            self.logger.debug("Encountered error while shutting down")

    def point_cloud_received(self, point_cloud):
        pass

    def _teardown(self):
        if self._is_open():
            try:
                self._set_opmode_monitor_request()
                self._set_session_baud(DEFAULT_SICK_LMS_SICK_BAUD)
            except BaseException:
                self._teardown_connection()
                raise
            self._teardown_connection()

    def _setup_connection(self):
        self.serial_ref = serial.Serial(
            port=self.device_path,
            baudrate=DEFAULT_SICK_LMS_SICK_BAUD,
            timeout=DEFAULT_SICK_LMS_SICK_MESSAGE_TIMEOUT
        )

    def _teardown_connection(self):
        if self._is_open():
            self.serial_ref.close()

    def _is_open(self):
        return self.serial_ref is not None and self.serial_ref.isOpen()

    def _set_session_baud(self, baud):
        self.session_baud = baud

        if baud not in sick_lms_baud_codes:
            raise SickConfigException("Invalid baud rate: %s" % baud)
        payload = b'\x20'
        payload += Message.int_to_byte(sick_lms_baud_codes[baud], 1)
        self.send_message.payload = payload

        self._send_message_and_get_reply(self.send_message.make_buffer())
        self._set_terminal_baud(baud)
        time.sleep(0.25)
        self.serial_ref.flush()

    def _test_baud(self, baud):
        self._set_terminal_baud(baud)

        try:
            error_type_buffer, error_num_buffer = self._get_errors()
            if len(error_num_buffer) > 0 or len(error_num_buffer) > 0:
                self.logger.debug("Encountered errors: %s, %s" % (error_type_buffer, error_num_buffer))
        except (SickConfigException, SickTimeoutException, SickIOException):
            self.logger.debug("Encountered errors when testing baud")
            return False

        return True

    def _get_errors(self):
        payload = b'\x32'
        self.send_message.payload = payload

        response = self._send_message_and_get_reply(self.send_message.make_buffer())

        num_errors = int((len(response.payload) - 2) / 2)

        k = 1
        error_type_buffer = []
        error_num_buffer = []
        for index in range(num_errors):
            error_type_buffer.append(response.payload[k])
            k += 1

            error_num_buffer.append(response.payload[k])
            k += 1

        return error_type_buffer, error_num_buffer

    def set_measuring_units(self, units: int = SICK_MEASURING_UNITS_MM):
        if is_valid_measuring_units(units) and units != self.config.measuring_units:
            self.config.measuring_units = units

    def set_sensitivity(self, sensitivity=SICK_SENSITIVITY_STANDARD):
        if not is_valid_sensitivity(sensitivity):
            raise SickConfigException("Invalid sensitivity input: %s" % repr(sensitivity))

        if sensitivity != self.config.peak_threshold:
            self.config.peak_threshold = sensitivity

    def set_measuring_mode(self, measuring_mode=SICK_MS_MODE_8_OR_80_FA_FB_DAZZLE):
        if not is_valid_measuring_mode(measuring_mode):
            raise SickConfigException("Undefined measuring mode: '%s'" % repr(measuring_mode))

        if measuring_mode != self.config.measuring_mode:
            self.config.measuring_mode = measuring_mode

    def set_availability(self, availability_flag=SICK_FLAG_AVAILABILITY_DEFAULT):
        if availability_flag > 7:
            raise SickConfigException("Invalid availability: %s" % repr(availability_flag))

        if availability_flag != self.config.availability_level:
            # Maintain the higher level bits
            self.config.availability_level &= 0xf8

            # Set the new availability flags
            self.config.availability_level |= availability_flag

    def set_variant(self, scan_angle, scan_resolution):
        if self.sick_type == SICK_LMS_TYPE_211_S14 or \
                        self.sick_type == SICK_LMS_TYPE_221_S14 or \
                        self.sick_type == SICK_LMS_TYPE_291_S14:
            raise SickConfigException("Command not supported on this model!")

        if not is_valid_scan_angle(scan_angle):
            raise SickConfigException("Undefined scan angle: %s" % repr(scan_angle))

        if not is_valid_scan_resolution(scan_resolution):
            raise SickConfigException("Undefined scan resolution: %s" % repr(scan_resolution))

        if self.operating_status.scan_angle != scan_angle or self.operating_status.scan_resolution != scan_resolution:
            payload = b'\x3b'
            payload += sick_lms_scan_angles[scan_angle]
            payload += sick_lms_scan_resolutions[scan_resolution]

            self.send_message.payload = payload

            # This is done since the Sick stops sending data if the variant is reset midstream.
            self._set_opmode_monitor_request()

            response = self._send_message_and_get_reply(self.send_message.make_buffer())
            if response.payload[1] != 0x01:
                raise SickConfigException("Configuration was unsuccessful!")

            self.operating_status.scan_angle = response.parse_int(2, 2)
            self.operating_status.scan_resolution = response.parse_int(4, 2)

            self.angles = np.arange(0, self.operating_status.scan_angle, self.operating_status.scan_resolution)

            self._switch_opmode(self.session_mode, self.session_mode_params)

    def get_scan(self, reflect_values=False):
        self._set_opmode_monitor_stream()
        response = self._recv_message()
        if reflect_values:
            if response.payload[0] != 0xc4:
                raise SickIOException("Invalid response for current measurement mode: %s" % response)
            self.c4_scan.parse_scan_profile(response.payload[1:], self.operating_status.measuring_mode)
            self.current_scan = self.c4_scan
        else:
            if response.payload[0] != 0xb0:
                raise SickIOException("Invalid response for current measurement mode: %s" % response)
            self.b0_scan.parse_scan_profile(response.payload[1:], self.operating_status.measuring_mode)
            self.current_scan = self.b0_scan

        self.distances = np.array(self.current_scan.measurements[:self.current_scan.num_measurements])

    def get_scan_subrange(self, start_index, stop_index):
        self._set_opmode_monitor_stream_subrange(start_index, stop_index)
        response = self._recv_message()
        if response.payload[0] != 0xb7:
            raise SickIOException("Invalid response for current measurement mode: %s" % response)

        self.b7_scan.parse_scan_profile(response.payload[1:], self.operating_status.measuring_mode)
        self.current_scan = self.b7_scan

        self.distances = np.array(self.current_scan.measurements[:self.current_scan.num_measurements])

    def get_partial_scan(self):
        self._set_opmode_monitor_stream_partial_scan()
        response = self._recv_message()
        if response.payload[0] != 0xb0:
            raise SickIOException("Invalid response for current measurement mode: %s" % response)

        self.b0_scan.parse_scan_profile(response.payload[1:], self.config.measuring_mode)
        self.current_scan = self.b0_scan

        self.distances = np.array(self.current_scan.measurements[:self.current_scan.num_measurements])

    def get_mean_values(self, sample_size):
        self._set_opmode_monitor_stream_mean(sample_size)
        response = self._recv_message()
        if response.payload[0] != 0xb6:
            raise SickIOException("Invalid response for current measurement mode: %s" % response)

        self.b6_scan.parse_scan_profile(response.payload[1:], self.config.measuring_mode)
        self.current_scan = self.b6_scan

        self.distances = np.array(self.current_scan.measurements[:self.current_scan.num_measurements])

    def get_mean_values_subrange(self, sample_size, start_index, stop_index):
        self._set_opmode_monitor_stream_mean_subrange(sample_size, start_index, stop_index)
        response = self._recv_message()
        if response.payload[0] != 0xb7:
            raise SickIOException("Invalid response for current measurement mode: %s" % response)

        self.b7_scan.parse_scan_profile(response.payload[1:], self.config.measuring_mode)
        self.current_scan = self.b7_scan

        self.distances = np.array(self.current_scan.measurements[:self.current_scan.num_measurements])

    def _set_opmode_installation(self):
        self._switch_opmode(SICK_OP_MODE_INSTALLATION, DEFAULT_SICK_LMS_SICK_PASSWORD)
        self.logger.debug("Successfully entered installation mode")

    def _set_opmode_diagnostic(self):
        self._switch_opmode(SICK_OP_MODE_DIAGNOSTIC)

    def _set_opmode_monitor_request(self):
        self._switch_opmode(SICK_OP_MODE_MONITOR_REQUEST_VALUES)

    def _set_opmode_monitor_stream(self):
        self._switch_opmode(SICK_OP_MODE_MONITOR_STREAM_VALUES)

    def _set_opmode_monitor_stream_range_reflectivity(self):
        self._switch_opmode(SICK_OP_MODE_MONITOR_STREAM_RANGE_AND_REFLECT, [0x01, 0x00, 0xB5, 0x00])

    def _set_opmode_monitor_stream_partial_scan(self):
        self._switch_opmode(SICK_OP_MODE_MONITOR_STREAM_VALUES_FROM_PARTIAL_SCAN)

    def _set_opmode_monitor_stream_mean(self, sample_size):
        if not (2 < sample_size < 250):
            raise SickConfigException("Invalid sample size: %s" % repr(sample_size))
        if self.mean_sample_size != sample_size:
            self.mean_sample_size = sample_size

            mode_params = Message.int_to_byte(sample_size, 1)
            self._switch_opmode(SICK_OP_MODE_MONITOR_STREAM_VALUES_FROM_PARTIAL_SCAN, mode_params)

    def _set_opmode_monitor_stream_subrange(self, start_index, stop_index):
        if self.subrange_start_index != start_index or self.subrange_stop_index != stop_index:
            max_subrange_stop_index = self.operating_status.scan_angle * 100 / self.operating_status.scan_resolution + 1
            if start_index > stop_index or start_index == 0 or stop_index > max_subrange_stop_index:
                raise SickConfigException("Invalid subregion bounds")

            self.subrange_start_index = start_index
            self.subrange_stop_index = stop_index

            mode_params = Message.int_to_byte(start_index, 2)
            mode_params += Message.int_to_byte(stop_index, 2)

            self._switch_opmode(SICK_OP_MODE_MONITOR_STREAM_VALUES_SUBRANGE, mode_params)

    def _set_opmode_monitor_stream_mean_subrange(self, sample_size, start_index, stop_index):
        if self.subrange_start_index != start_index or \
                        self.subrange_stop_index != stop_index or \
                        self.mean_sample_size != sample_size:
            if not (2 < sample_size < 250):
                raise SickConfigException("Invalid sample size: %s" % repr(sample_size))

            max_subrange_stop_index = self.operating_status.scan_angle * 100 / self.operating_status.scan_resolution + 1
            if start_index > stop_index or start_index == 0 or stop_index > max_subrange_stop_index:
                raise SickConfigException("Invalid subregion bounds")

            self.mean_sample_size = sample_size
            self.subrange_start_index = start_index
            self.subrange_stop_index = stop_index

            mode_params = Message.int_to_byte(sample_size, 1)
            mode_params += Message.int_to_byte(start_index, 2)
            mode_params += Message.int_to_byte(stop_index, 2)

            self._switch_opmode(SICK_OP_MODE_MONITOR_STREAM_MEAN_VALUES_SUBRANGE, mode_params)

    def _switch_opmode(self, mode: int, mode_params=None):
        if self.operating_status.operating_mode == mode:
            return

        payload_buffer = b'\x20'
        payload_buffer += Message.int_to_byte(mode, 1)

        if mode_params is not None:
            payload_buffer += mode_params
        message = Message(payload_buffer)

        response = self._send_message_and_get_reply(message.make_buffer())
        if len(response.payload) < 2 or response.payload[1] != 0x00:
            raise SickConfigException("configuration request failed! Here's the response: %s" % response)

        self.operating_status.operating_mode = mode

    def _get_status(self):
        self.send_message.payload = b'\x31'
        response = self._send_message_and_get_reply(self.send_message.make_buffer())
        self.operating_status.parse_status(response)

        scan_angle_radians = math.radians(self.operating_status.scan_angle)
        resolution_radians = math.radians(self.operating_status.scan_resolution * 0.01)

        self.angles = np.arange(0, scan_angle_radians + resolution_radians, resolution_radians)

    def _get_config(self):
        self.send_message.payload = b'\x74'
        response = self._send_message_and_get_reply(self.send_message.make_buffer())
        self.config.parse_config_profile(response)

    def update_config(self):
        self._set_opmode_installation()

        telegram = self.config.build_message()
        self.logger.debug("Setting new configuration")
        response = self._send_message_and_get_reply(telegram.make_buffer())
        if response.payload[1] != 0x01:
            raise SickConfigException("Configuration failed!")

        self._get_status()

        self._switch_opmode(self.session_mode, self.session_mode_params)

    def _get_type(self):
        self.send_message.payload = b'\x3a'
        response = self._send_message_and_get_reply(self.send_message.make_buffer())

        model_string = response.parse_string(1)

        if model_string in supported_models:
            self.sick_type = supported_models[model_string]
        else:
            self.logger.debug("LMS is of an unknown type: %s" % model_string)
            self.sick_type = SICK_LMS_TYPE_UNKNOWN

    def reset(self):
        self.send_message.payload = b'\x10'
        self._send_message_and_get_reply(self.send_message.make_buffer(), 60, reply_code=0x91)
        self._set_terminal_baud(DEFAULT_SICK_LMS_SICK_BAUD)

        response = self._recv_message(timeout=30)

        if response.code != 0x90:
            self.logger.warning("Unexpected reply! (assuming device has been reset)")

        self.start()

    def _set_terminal_baud(self, baud):
        self.serial_ref.baudrate = baud

    def _send_message_and_get_reply(self, message: bytes, timeout=DEFAULT_SICK_LMS_SICK_MESSAGE_TIMEOUT,
                                    num_tries=DEFAULT_SICK_LMS_NUM_TRIES, reply_code=None) -> Message:
        self.logger.debug("writing: %s" % message)
        self.serial_ref.write(message)

        if not self._check_for_ack():
            raise SickConfigException("Command not received correctly!")

        response = None
        for _ in range(num_tries):
            try:
                response = self._recv_message(timeout)
                break
            except SickTimeoutException:
                pass
        if response is None:
            raise SickTimeoutException("Failed to get reply after %s attempts" % num_tries)

        if reply_code is not None:
            if response.code != reply_code:
                raise SickConfigException("Reply code doesn't match!")

        return response

    def _recv_message(self, timeout=DEFAULT_SICK_LMS_SICK_MESSAGE_TIMEOUT) -> Message:
        if timeout != self.serial_ref.timeout:
            self.serial_ref.timeout = timeout

        self.recv_message.reset()
        self.recording_buffer = ""

        if self._read_8() == 0x02:
            if self._read_8() == 0x80:
                length = self._read_16()
                payload = self._read(length)
                checksum = self._read_16()

                self.recv_message.make_message(payload, checksum)
                # self.logger.debug("[buffer] <%s>" % self.recording_buffer)

        if timeout != DEFAULT_SICK_LMS_SICK_MESSAGE_TIMEOUT:
            self.serial_ref.timeout = DEFAULT_SICK_LMS_SICK_MESSAGE_TIMEOUT

        return self.recv_message

    def _check_for_ack(self):
        ack = b'\x00'
        while ack == b'\x00':
            ack = self.serial_ref.read(1)
            if len(ack) > 0:
                if ack == b'\x06':
                    return True
                elif ack == b'\x15':
                    return False

        raise SickIOException("Invalid value received (neither ACK, nor NACK): " + repr(ack))

    def _read(self, num_bytes) -> bytes:
        with self.serial_lock:
            result = b''
            if self._is_open():
                result = self.serial_ref.read(num_bytes)
            else:
                raise SickIOException("Serial not open for reading!")

        if len(result) == 0:
            raise SickTimeoutException("Failed to read serial!")

        self.recv_message.append_byte(result)
        self.recording_buffer += ("%02x" * len(result)) % tuple([b for b in result])
        return result

    def _read_8(self) -> int:
        return ord(self._read(1))

    def _read_16(self) -> int:
        lower_byte = self._read_8()
        upper_byte = self._read_8()

        return (upper_byte << 8) + lower_byte

    def _is_lms200(self):
        return supported_models[self.sick_type][3:6] == "200"

    def _is_lms211(self):
        return supported_models[self.sick_type][3:6] == "211"

    def _is_lms220(self):
        return supported_models[self.sick_type][3:6] == "220"

    def _is_lms221(self):
        return supported_models[self.sick_type][3:6] == "221"

    def _is_lms291(self):
        return supported_models[self.sick_type][3:6] == "291"

    def _is_unknown(self):
        return self.sick_type == SICK_LMS_TYPE_UNKNOWN

    def _parse_point_cloud(self):
        self.point_cloud = np.vstack(
            [self.distances * np.cos(self.angles), self.distances * np.sin(self.angles)]).T

    def status_string(self):
        return "'%s' status:\n" \
               "Variant: %s\n" \
               "Type: %s\n" \
               "Sensor status: %s\n" \
               "Scan angle: %sº\n" \
               "Scan resolution: %sº\n" \
               "Operating mode: %s\n" \
               "Measuring mode: %s\n" \
               "Measuring units: %s\n" % (
                   self.name, variant_to_string(self.operating_status.variant), supported_models[self.sick_type],
                   status_to_string(self.operating_status.device_status), self.operating_status.scan_angle,
                   self.operating_status.scan_resolution * 0.01,
                   sick_lms_operating_modes[self.operating_status.operating_mode],
                   sick_lms_measuring_modes[self.operating_status.measuring_mode],
                   sick_lms_measuring_units[self.operating_status.measuring_units]
               )

    def __str__(self):
        return self.status_string()
