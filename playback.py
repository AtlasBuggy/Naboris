from atlasbuggy import Orchestrator, run
from atlasbuggy.plotters import LivePlotter, PlotMessage

from naboris.actuators_playback import ActuatorsPlayback


class PlaybackOrchestrator(Orchestrator):
    def __init__(self, event_loop):
        self.set_default(level=10)
        super(PlaybackOrchestrator, self).__init__(event_loop)

        actuators = ActuatorsPlayback("logs/2017_Nov_10/Actuators/15_59_42.log")
        plotter = LivePlotter()

        bno055_plot_name = plotter.add_plot("bno055", service=actuators.bno055_service)
        encoder_plot_name = plotter.add_plot("encoder", service=actuators.encoder_service)

        self.add_nodes(actuators, plotter)

        self.subscribe(actuators, plotter, bno055_plot_name, self.bno_to_plot)
        self.subscribe(actuators, plotter, encoder_plot_name, self.enc_to_plot)

        self.theta = 0.0

    def bno_to_plot(self, bno_message):
        return PlotMessage(bno_message.packet_time, bno_message.euler.z)

    def enc_to_plot(self, enc_message):
        if enc_message.delta_theta is not None:
            self.theta += enc_message.delta_theta
        return PlotMessage(enc_message.timestamp, self.theta)


run(PlaybackOrchestrator)
