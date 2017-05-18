import asyncio
from actuators import Actuators
from atlasbuggy.datastreams.serialstream import SerialStream
from atlasbuggy.datastreams.iostream.cmdline import CommandLine

actuators = Actuators()
serial = SerialStream(actuators, debug=True)
cmdline = CommandLine(True)


loop = asyncio.get_event_loop()
cmdline.asyncio_loop = loop

serial.start()
cmdline.start()

try:
    tasks = asyncio.gather(serial.run(), cmdline.run())
    loop.run_until_complete(tasks)
except KeyboardInterrupt:
    tasks.cancel()
    loop.run_forever()
    tasks.exception()
finally:
    loop.close()

serial.close()
cmdline.close()
loop.close()
