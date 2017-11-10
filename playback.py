from atlasbuggy import Orchestrator, run
from atlasbuggy.plotters import LivePlotter

from naboris.actuators_playback import ActuatorsPlayback


class PlaybackOrchestrator(Orchestrator):
    def __init__(self, event_loop):
        self.set_default(level=10)
        super(PlaybackOrchestrator, self).__init__(event_loop)

        actuators = ActuatorsPlayback("logs/2017_Nov_10/Actuators/15_59_42.log")
        plotter = LivePlotter()

        self.add_nodes(actuators, plotter)

        self.subscribe(actuators, plotter, plotter.xy, actuators.bno055_service)
        self.subscribe(actuators, plotter, plotter.xy, actuators.encoder_service)


run(PlaybackOrchestrator)
