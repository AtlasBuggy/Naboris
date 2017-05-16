from atlasbuggy.datastreams.core.serialstream import SerialStream
from actuators import Actuators

actuators = Actuators()
serial = SerialStream(actuators, debug=True)

serial.start()
try:
    while True:
        serial.update()
except KeyboardInterrupt:
    pass

serial.close()
