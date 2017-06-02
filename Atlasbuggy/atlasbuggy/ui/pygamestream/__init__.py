import asyncio
import pygame
from threading import Event
from atlasbuggy.datastream import DataStream


class PygameStream(DataStream):
    pygame_initialized = False
    pygame_exit_event = Event()

    def __init__(self, width, height, fps, enabled, debug, debug_name=None, display_flags=0, display_depth=0):
        super(PygameStream, self).__init__(enabled, debug, False, True, debug_name)
        self.fps = fps
        self.delay = 1 / fps
        self.width = width
        self.height = height
        self.display_size = (width, height)
        self.display = pygame.display.set_mode(self.display_size, display_flags, display_depth)

    def start(self):
        self.init_pygame()

    @staticmethod
    def init_pygame():
        if not PygameStream.pygame_initialized:
            pygame.init()

    def event(self, event):
        pass

    async def run(self):
        while self.all_running():
            pygame.event.pump()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.exit()
                    break

                self.event(event)
            self.update()

            pygame.display.flip()

            await asyncio.sleep(self.delay)
        self.quit_pygame()

    def quit_pygame(self):
        if not PygameStream.pygame_exit_event.is_set():
            PygameStream.pygame_exit_event.set()
            pygame.quit()
