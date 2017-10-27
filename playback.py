from atlasbuggy import Orchestrator, run

from naboris.actuators_playback import ActuatorsPlayback


class PlaybackOrchestrator(Orchestrator):
    def __init__(self, event_loop):
        super(PlaybackOrchestrator, self).__init__(event_loop)

        actuators = ActuatorsPlayback("logs/2017_Oct_27/Actuators/00_33_37.log")

        self.add_nodes(actuators)

run(PlaybackOrchestrator)