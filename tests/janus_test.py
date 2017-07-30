from atlasbuggy.janus import Queue
from threading import Thread, Event
import asyncio
import time

loop = asyncio.get_event_loop()
queue = Queue(loop=loop)
exit_event = Event()


async def async_put_coro(async_q):
    counter = 0
    while not exit_event.is_set():
        await async_q.put(counter)
        counter += 1
        # await asyncio.sleep(0.1)
    async_q.join()


def sync_get_coro(sync_q):
    while not exit_event.is_set():
        while not sync_q.empty():
            print("sync:", sync_q.get())
            sync_q.task_done()


async def async_get_coro(async_q):
    while not exit_event.is_set():
        while not async_q.empty():
            print("async:", await async_q.get())
            async_q.task_done()
            await asyncio.sleep(0.1)

    await async_q.join()


def sync_put_coro(sync_q):
    counter = 0
    while not exit_event.is_set():
        sync_q.put(counter)
        counter += 1
        time.sleep(0.1)
    sync_q.join()


async def main_coro():
    while not exit_event.is_set():
        print("size:", queue.async_q.qsize())
        await asyncio.sleep(0.1)


thread = Thread(target=sync_get_coro, args=(queue.sync_q,))
coroutine = asyncio.gather(*[main_coro(), async_put_coro(queue.async_q)])

try:
    thread.start()
    loop.run_until_complete(coroutine)
except KeyboardInterrupt:
    exit_event.set()
thread.join()
