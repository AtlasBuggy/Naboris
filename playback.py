import math

from atlasbuggy import Orchestrator, run
from atlasbuggy.plotters import LivePlotter, PlotMessage

from naboris.actuators_playback import ActuatorsPlayback


class PlaybackOrchestrator(Orchestrator):
    def __init__(self, event_loop):
        self.set_default(level=30)
        super(PlaybackOrchestrator, self).__init__(event_loop)

        # path = "logs/2017_Nov_10/Actuators/19_52_25.log"
        path = "logs/2017_Nov_11/Actuators/00_54_34.log"

        self.actuators = ActuatorsPlayback(path)
        self.plotter = LivePlotter()

        bno055_plot_name = self.plotter.add_plot("bno055", service=self.actuators.bno055_service)
        encoder_plot_name = self.plotter.add_plot("encoder", service=self.actuators.encoder_service)

        self.add_nodes(self.actuators, self.plotter)

        self.subscribe(self.actuators, self.plotter, bno055_plot_name, self.bno_to_plot)
        self.subscribe(self.actuators, self.plotter, encoder_plot_name, self.enc_to_plot)

        self.theta = 0.0
        self.x = 0.0
        self.y = 0.0

    def bno_to_plot(self, bno_message):
        return PlotMessage(bno_message.packet_time, bno_message.euler.z)

    def enc_to_plot(self, enc_message):
        if enc_message.delta_theta is not None:
            self.theta += enc_message.delta_theta
            self.theta %= 2 * math.pi
            strafe_angle = math.radians(self.actuators.commanded_angle)

            angle = (self.theta + strafe_angle) % (2 * math.pi)
            self.x += enc_message.delta_dist * math.cos(angle)
            self.y += enc_message.delta_dist * math.sin(angle)

        # return PlotMessage(enc_message.timestamp, self.theta)
        return PlotMessage(self.x, self.y)


run(PlaybackOrchestrator)
