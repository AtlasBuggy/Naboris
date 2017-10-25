import re
import os
import asyncio
from queue import Queue
from pymouse import PyMouseEvent, PyMouse

from atlasbuggy import Node, Message


os.environ["SDL_VIDEODRIVER"] = "dummy"
os.putenv('SDL_VIDEODRIVER', 'fbcon')

class MouseMessage(Message):
    message_regex = r"MouseMessage\(t=(\d.*), n=(\d*), dx=(\d.*), dy=(\d.*)\)"

    def __init__(self, dx, dy, timestamp=None, n=0):
        super(MouseMessage, self).__init__(timestamp, n)
        self.dx = dx
        self.dy = dy

    @classmethod
    def parse(cls, message):
        match = re.match(cls.message_regex, message)
        if match is not None:
            message_time = float(match.group(1))
            n = int(match.group(2))
            dx = int(match.group(3))
            dy = int(match.group(4))

            return MouseMessage(dx, dy, message_time, n)
        else:
            return None

    def __str__(self):
        return "%s(t=%s, n=%s, dx=%s, dy=%s)" % (self.__class__.__name__, self.timestamp, self.n, self.dx, self.dy)


class MouseEventHandler(PyMouseEvent):
    def __init__(self):
        super(MouseEventHandler, self).__init__()

        self.m = PyMouse()
        self.x_dim, self.y_dim = self.m.screen_size()

        self.x_lower = self.x_dim / 4
        self.x_upper = 3 * self.x_dim / 4

        self.y_lower = self.y_dim / 4
        self.y_upper = 3 * self.y_dim / 4

        self.x_reset = self.x_dim / 2
        self.y_reset = self.y_dim / 2

        self.m.move(self.x_reset, self.y_reset)
        self.prev_x = self.x_reset
        self.prev_y = self.y_reset

        self.current_x = self.x_reset
        self.current_y = self.y_reset

        self.message_num = 0
        self.mouse_messages = Queue()

    def move(self, x, y):
        self.prev_x = self.current_x
        self.prev_y = self.current_y

        self.current_x = x
        self.current_y = y

        if not (self.x_lower < x < self.x_upper) or not (self.y_lower < y < self.y_upper):
            x_diff = x - self.x_reset
            y_diff = y - self.y_reset

            self.prev_x -= x_diff
            self.prev_y -= y_diff

            self.current_x -= x_diff
            self.current_y -= y_diff

            self.m.move(self.x_reset, self.y_reset)

        dx = self.current_x - self.prev_x
        dy = self.current_y - self.prev_y

        self.mouse_messages.put(MouseMessage(dx, dy, n=self.message_num))

        self.message_num += 1


class MouseSensor(Node):
    def __init__(self, enabled=True):
        super(MouseSensor, self).__init__(enabled)
        self.event_handler = MouseEventHandler()

    async def setup(self):
        self.event_handler.start()

    async def loop(self):
        while True:
            if not self.event_handler.mouse_messages.empty():
                while not self.event_handler.mouse_messages.empty():
                    await self.broadcast(self.event_handler.mouse_messages.get())
            else:
                await asyncio.sleep(0.01)

    async def stop(self):
        self.event_handler.stop()


if __name__ == '__main__':
    import time
    from atlasbuggy import Orchestrator, run


    class TestConsumer(Node):
        def __init__(self):
            super(TestConsumer, self).__init__()
            self.mouse_tag = "mouse"
            self.mouse_queue = None
            self.mouse_sub = self.define_subscription(self.mouse_tag)

        def take(self):
            self.mouse_queue = self.mouse_sub.get_queue()

        async def loop(self):
            while True:
                message = await self.mouse_queue.get()
                print("dx=%0.4f, dy=%0.4f, delay=%0.4f" % (message.dx, message.dy, time.time() - message.timestamp))


    class TestOrchestrator(Orchestrator):
        def __init__(self, event_loop):
            super(TestOrchestrator, self).__init__(event_loop)
            sensor = MouseSensor()
            consumer = TestConsumer()

            self.add_nodes(sensor, consumer)
            self.subscribe(sensor, consumer, consumer.mouse_tag)


    run(TestOrchestrator)
