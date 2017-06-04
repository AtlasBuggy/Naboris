from atlasbuggy.serial.file import SerialFile
from atlasbuggy.ui.plotters.plot import RobotPlot
from atlasbuggy.ui.plotters.collection import RobotPlotCollection


class NaborisSimulator(SerialFile):
    def __init__(self, naboris, file_name, directory, plotter):
        self.naboris = naboris
        super(NaborisSimulator, self).__init__(naboris, file_name, directory)

        self.current_frame = 0
        self.plotter = plotter

    # def update(self):
    #     time.sleep(0.03)

    def receive_first(self, whoiam, packet):
        if whoiam == self.naboris.actuators.whoiam:
            self.plotter.add_plot(self.naboris.actuators.strip_plot)

    def receive_command(self, whoiam, timestamp, packet):
        if whoiam == self.naboris.actuators.whoiam:
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
                start_led = int(packet[1:4])
                r = int(packet[4:7])
                g = int(packet[7:10])
                b = int(packet[10:13])
                if len(packet) > 13:
                    end_led = int(packet[13:16])
                    if self.naboris.actuators.strip_plot.enabled:
                        for led_num in range(start_led, end_led):
                            self.naboris.actuators.led_plots[led_num].set_properties(color=(r / 255, g / 255, b / 255))
                else:
                    if self.naboris.actuators.strip_plot.enabled:
                        self.naboris.actuators.led_plots[start_led].set_properties(color=(r / 255, g / 255, b / 255))

    def receive_user(self, whoiam, timestamp, packet):
        if whoiam == "NaborisCam":
            self.current_frame = int(packet)
            # elif whoiam == "frame check":
            #     num_frames, frame = packet.split("\t")
            #     print("check:", num_frames)

            # def file_finished(self):
            #     self.exit()
