import serial
from threading import Lock
from serial.serialutil import SerialException
from atlasbuggy.datastream import DataStream


class LMS200(DataStream):
    def __init__(self, port, enabled=True, debug=False, baud=9600):
        super(LMS200, self).__init__(enabled, debug, True, False)

        self.port_address = port
        self.baud_rate = baud
        self.serial_ref_timeout = 1.0
        self.serial_ref = None
        self.read_lock = Lock()

    def open_port(self):
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

    def write_telegram(self, address, packet):
        self.serial_ref.flush()
        self.serial_ref.write(self.generate_telegram(address, packet))

        while True:
            ack = self.serial_ref.read(1)
            if len(ack) > 0:
                if ack == b'\x06':
                    return True
                elif ack == b'\x15':
                    return False
                else:
                    self.debug_print("Invalid value received (neither ACK, nor NACK)", repr(ack))

    def write_reset(self):
        self.write_telegram(0, b'\x10')

    def write_start(self):
        self.write_telegram(0, b'\x20\x20')

    def start(self):
        self.open_port()
        self.write_start()

    def run(self):
        print("Reading serial port '%s'..." % self.port_address)

        while self.all_running():
            with self.read_lock:
                data = self.serial_ref.read(self.serial_ref.inWaiting())
            if len(data) > 0:
                self.process_data(data)
        self.exit()

    def process_data(self, data):
        pass

    def close(self):
        with self.read_lock:
            self.write_reset()
        self.serial_ref.close()
