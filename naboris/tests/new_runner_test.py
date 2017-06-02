import asyncio

from atlasbuggy.serialstream import SerialStream
from atlasbuggy.uistream.cmdline import CommandLine

from naboris.actuators import Actuators

actuators = Actuators()
serial = SerialStream(actuators, debug=True)
cmdline = CommandLine(True, False)


loop = asyncio.get_event_loop()
cmdline.asyncio_loop = loop

serial.start()
cmdline.start()

tasks = asyncio.gather(serial.run(), cmdline.run())

try:
    loop.run_until_complete(tasks)
except KeyboardInterrupt:
    tasks.cancel()
finally:
    loop.close()

serial.close()
cmdline.close()
loop.close()
