import math
import random
import asyncio

from atlasbuggy.serial import SerialStream

from naboris.soundfiles import SoundStream
from naboris.actuators import Actuators
from atlasbuggy.plotters.liveplotter import LivePlotter
from atlasbuggy.plotters.plot import RobotPlot
from atlasbuggy.plotters.collection import RobotPlotCollection
from atlasbuggy.plotters.staticplotter import StaticPlotter


class Naboris(SerialStream):
    def __init__(self, enabled=True, log_level=None, plot=False):
        self.actuators = Actuators()
        super(Naboris, self).__init__(self.actuators, enabled=enabled, log_level=log_level)

        self.link_callback(self.actuators, self.receive_actuators)
        self.link_recurring(10, self.request_battery)
        self.link_recurring(1, self.event_random_sound, include_event_in_params=True)
        self.link_recurring(0.1, self.led_clock)
        self.led_index = 0
        self.prev_led_state = None

        self.sounds = SoundStream("sounds", "/home/pi/Music/Bastion/")
        self.random_sound_folders = ["humming", "curiousity", "nothing", "confusion", "concern", "sleepy", "vibrating"]

        self.led_plot = RobotPlotCollection("led plot")
        self.plotter = None
        self.should_plot = plot

    def serial_start(self):
        self.actuators.set_all_leds(5, 5, 5)
        self.actuators.set_battery(5050, 5180)

    def take(self):
        if self.should_plot:
            self.plotter = self.streams["plotter"]
            self.plotter.add_plots(self.led_plot)

    async def update(self):
        if self.plotter is not None:
            if isinstance(self.plotter, StaticPlotter):
                await asyncio.sleep(0.0)
            elif isinstance(self.plotter, LivePlotter):
                await asyncio.sleep(0.001)

    def event_random_sound(self, event):
        event.repeat_time = random.randint(30, 120)  # play a random sound every 30..120 seconds
        self.play_random_sound()

    def play_random_sound(self):
        folder = random.choice(self.random_sound_folders)
        sound = random.choice(self.sounds.list_sounds(folder))
        self.sounds.play(sound)

    def receive_actuators(self, timestamp, packet):
        if timestamp is None:
            if self.plotter is not None:
                num_leds = self.actuators.num_leds
                for index in range(num_leds):
                    led = RobotPlot("LED #%s" % index, marker='.', markersize=10, markeredgecolor='black',
                                    x_range=(-2, 2), y_range=(-2, 2), color='black')
                    self.led_plot.add_plot(led)

                    led.append(math.cos(-index / num_leds * 2 * math.pi), math.sin(-index / num_leds * 2 * math.pi))
                self.plotter.update_collection(self.led_plot)

    def received_log(self, timestamp, whoiam, packet, packet_type):
        if whoiam == self.actuators.whoiam:
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
                if self.plotter is not None and self.led_plot.enabled:
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

    def led_clock(self):
        self.prev_led_state = self.actuators.get_led(self.led_index)

        self.actuators.set_led(self.led_index, 0, 128, 255, show=False)
        self.actuators.set_led((self.led_index - 1) % self.actuators.num_leds, self.prev_led_state)

        self.led_index += 1
        if self.led_index >= self.actuators.num_leds:
            self.led_index = 0

    def request_battery(self):
        self.actuators.ask_battery()

    def serial_close(self):
        self.actuators.stop()
        self.actuators.release()

        if self.plotter is not None:
            if isinstance(self.plotter, StaticPlotter):
                self.exit()
                self.plotter.plot()
            elif isinstance(self.plotter, LivePlotter):
                self.plotter.plot()
