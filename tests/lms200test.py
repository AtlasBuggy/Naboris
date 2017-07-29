import binascii
import serial
import threading

# =============================================================================

SERIAL_PORT = '/dev/cu.usbserial'
# NB: Different crystal, x8 multiplier
SERIAL_BAUDRATE = 9600  # int(500000 * 14745600 / 16000000 / 8)
SERIAL_TIMEOUT = 1


# =============================================================================

def lms200_crc(data):
    crc16 = 0
    byte = [0, 0]
    for c in data:
        byte[1] = byte[0]
        byte[0] = c

        if (crc16 & 0x8000):
            crc16 = (crc16 & 0x7FFF) << 1
            crc16 ^= 0x8005
        else:
            crc16 = crc16 << 1

        crc16 ^= (byte[1] << 8) | byte[0]

    return crc16


# =============================================================================

class LMS200Telegram(object):
    def __init__(self, data=None):
        if data:
            if len(data) < 7:
                raise RuntimeError("Invalid telegram size")
            if data[0] != b'\x02':
                raise RuntimeError("Invalid STX")
            self.address = ord(data[1])
            self.length = ord(data[2]) + (ord(data[3]) * 256)
            self.payload = data[4:-2]
            self.crc = ord(data[-2]) + (ord(data[-1]) * 256)
        else:
            self.address = 0
            self.length = 0
            self.payload = b''
            self.crc = 0

    def generate(self):
        data = b'\x02' + chr(self.address).encode()
        self.length = len(self.payload)
        data += chr(self.length & 0xFF).encode()
        data += chr((self.length >> 8) & 0xFF).encode()
        data += self.payload
        self.crc = lms200_crc(data)
        data += chr(self.crc & 0xFF).encode()
        data += chr((self.crc >> 8) & 0xFF).encode()
        return data


class LMS200Command(object):
    def __init__(self, payload):
        if len(payload) < 1:
            raise RuntimeError("Invalid payload size")
        self.opcode = ord(payload[0])
        self.body = payload[1:]


class LMS200Response(object):
    def __init__(self, payload):
        if len(payload) < 2:
            raise RuntimeError("Invalid payload size")
        self.opcode = ord(payload[0])
        self.status = ord(payload[-1])
        self.body = payload[1:-1]


# =============================================================================

def cmd_reset_sensor():
    t = LMS200Telegram()
    t.payload = b'\x10'
    return t


def cmd_start_measurement():
    t = LMS200Telegram()
    t.payload = b'\x20\x20'
    return t


# =============================================================================

class LMS200Interface(object):
    def __init__(self, port, baudrate, timeout):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial = None
        self.serial_rlock = threading.Lock()
        self.serial_wlock = threading.Lock()
        self.buffer = []

    def open_port(self):
        self.serial = serial.Serial(
            port=self.port,
            baudrate=self.baudrate,
            timeout=self.timeout
        )

    def close_port(self):
        self.write_telegram(cmd_reset_sensor())
        self.serial.close()
        self.serial = None

    def process_data(self, data):
        self.buffer += data

    def write_telegram(self, t):
        self.serial.flush()
        with self.serial_wlock:
            self.serial.write(t.generate())
        with self.serial_rlock:
            while True:
                ack = self.serial.read(1)
                if len(ack) > 0:
                    if ack == b'\x06':
                        return True
                    elif ack == b'\x15':
                        return False
                    else:
                        raise RuntimeError("Invalid value received (neither ACK, nor NACK)", repr(ack))

    def worker(self):
        if not self.serial:
            raise RuntimeError("Serial port not initialized.")

        print("Reading serial port '%s'..." % self.port)
        # self.write_telegram(cmd_reset_sensor())

        self.write_telegram(cmd_start_measurement())

        try:
            while not self.stop_flag:
                data = self.serial.read(1024)
                if len(data) > 0:
                    print("Got %d bytes." % len(data))
                    self.process_data(data)
        except KeyboardInterrupt:
            pass
        finally:
            lms.close_port()

    def run(self):
        lms.open_port()
        self.thread = threading.Thread(target=self.worker)
        self.stop_flag = False
        self.thread.start()

    def stop(self):
        self.stop_flag = True
        self.thread.join()
        lms.close_port()


# =============================================================================

lms = LMS200Interface(SERIAL_PORT, SERIAL_BAUDRATE, SERIAL_TIMEOUT)

try:
    lms.run()
except KeyboardInterrupt:
    lms.stop()
