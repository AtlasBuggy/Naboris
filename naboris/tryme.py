from atlasbuggy.logparser import LogParser
from atlasbuggy import Robot, DataStream
from atlasbuggy.plotters.liveplotter import LivePlotter
from atlasbuggy.subscriptions import *
from naboris import Naboris


class NaborisCamSimulator(DataStream):
    def __init__(self, enabled=True, log_level=10):
        super(NaborisCamSimulator, self).__init__(enabled, "NaborisCam", log_level)

    def receive_log(self, log_level, message, line_info):
        print(self.name, message)


def key_press_fn(event):
    if event.key == "q":
        plotter.exit()


robot = Robot()

log = LogParser("21;25;23.log.xz", "logs/2017_Jun_10", enabled=True, update_rate=0.001)
naboris = Naboris(demo=True)
camera = NaborisCamSimulator()
plotter = LivePlotter(1, matplotlib_events=dict(key_press_event=key_press_fn),
                      close_when_finished=True, enabled=True, fig_kwargs=dict(figsize=(5, 5)))

log.subscribe(Subscription("naboris (can be any non-overlapping tag name)", naboris))
log.subscribe(Subscription("camera", camera))
naboris.subscribe(Subscription(naboris.plotter_tag, plotter))

robot.run(log, plotter)
