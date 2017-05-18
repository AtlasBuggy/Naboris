import time
import sys
from atlasbuggy.datastreams.iostream import IOstream
import asyncio


class CommandLine(IOstream):
    def __init__(self, name, debug, prompt_text=">> "):
        super(CommandLine, self).__init__(name, debug)
        self.prompt_text = prompt_text
        self.queue = asyncio.Queue()

    def stream_start(self):
        self.asyncio_loop.add_reader(sys.stdin, self.handle_stdin)
        self.debug_print("Command line starting")

    def handle_stdin(self):
        data = sys.stdin.readline()
        asyncio.async(self.queue.put(data))

    async def run(self):
        while True:
            print("\r%s" % self.prompt_text, end="")
            data = await self.queue.get()
            await asyncio.sleep(0.01)
            self.handle_input(data.strip('\n'))

    def handle_input(self, line):
        if line == 'q':
            self.exit()
