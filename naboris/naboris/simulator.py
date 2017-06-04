import math
import asyncio
from atlasbuggy.serial.file import SerialFile
from atlasbuggy.ui.plotters.plot import RobotPlot
from atlasbuggy.ui.plotters.collection import RobotPlotCollection


class NaborisSimulator(SerialFile):
    def __init__(self, naboris, file_name, directory, plotter):
        self.naboris = naboris
        super(NaborisSimulator, self).__init__(naboris, file_name, directory)

        self.current_frame = 0
        self.plotter = plotter
        self.led_plot = RobotPlotCollection("led plot")
        self.plotter.add_plots(self.led_plot)

    async def update(self):
        await asyncio.sleep(0.001)

    def receive_first(self, whoiam, packet):
        if whoiam == self.naboris.actuators.whoiam:
            num_leds = self.naboris.actuators.num_leds
            for index in range(num_leds):
                led = RobotPlot("LED #%s" % index, marker='.', markersize=10,
                                x_range=(-2, 2), y_range=(-2, 2), color='black')
                self.led_plot.add_plot(led)

                led.append(math.cos(-index / num_leds * 2 * math.pi), math.sin(-index / num_leds * 2 * math.pi))
            self.plotter.update_collection(self.led_plot)
            self.plotter.set_time(self.start_time)

    def receive_command(self, whoiam, timestamp, packet):
        if whoiam == "naboris actuators":
            if packet == "h":
                print("%0.4fs:" % self.dt(), "stop")
            elif packet[0] == "r":
                print("%0.4fs:" % self.dt(), "spinning %s" % "right" if bool(int(packet[1:3])) else "left")
            elif packet[0] == "p":
                print(
                    "%0.4fs:" % self.dt(), "driving at %sº at speed %s" % (
                        (1 if packet[1] == "0" else -1) * int(packet[2:5]), int(packet[5:8]))
                )
            elif packet[0] == "c":
                yaw = int(packet[1:4])
                azimuth = int(packet[4:7])
                print("%0.4fs:" % self.dt(), end="looking ")
                if yaw == 90 and azimuth == 90:
                    print("straight")
                else:
                    if yaw > 90:
                        print("left and ", end="")
                    elif yaw < 90:
                        print("right and ", end="")

                    if azimuth == 90:
                        print("straight")
                    elif azimuth > 90:
                        print("up", end="")
                    else:
                        print("down", end="")

                    if yaw == 90:
                        print(" and straight", end="")
                    print()

            elif packet[0] == "o":
                if self.led_plot.enabled:
                    start_led = int(packet[1:4])
                    r = int(packet[4:7])
                    g = int(packet[7:10])
                    b = int(packet[10:13])
                    if len(packet) > 13:
                        end_led = int(packet[13:16])
                        for led_num in range(start_led, end_led):
                            self.led_plot[led_num].set_properties(color=(r / 255, g / 255, b / 255))
                    else:
                        self.led_plot[start_led].set_properties(color=(r / 255, g / 255, b / 255))
                    self.plotter.draw_text(
                        self.led_plot,
                        "Hi I'm naboris!\nThese are the LEDs states at t=%0.2fs" % (self.dt()),
                        0, 0, verticalalignment='center',  horizontalalignment='center', text_name="welcome text",
                        fontsize='small'
                    )

    def receive_user(self, whoiam, timestamp, packet):
        if whoiam == "NaborisCam":
            self.current_frame = int(packet)
            # elif whoiam == "frame check":
            #     num_frames, frame = packet.split("\t")
            #     print("check:", num_frames)
