import os
import argparse

from atlasbuggy import Orchestrator, run

from naboris.soundfiles import Sounds
from naboris.actuators import Actuators
from naboris.picamera import PiCamera
from naboris.cli import NaborisCLI
from naboris.naboris_site import NaborisWebsite
from naboris.mouse_sensor import MouseSensor

parser = argparse.ArgumentParser()
parser.add_argument("-l", "--log", help="disable logging", action="store_false")
args = parser.parse_args()

log = args.log


class NaborisOrchestrator(Orchestrator):
    def __init__(self, event_loop):
        self.set_default(write=log, level=30)
        super(NaborisOrchestrator, self).__init__(event_loop)

        video_file_name = self.file_name[:-3] + "mp4"

        video_directory = "videos/" + os.path.join(*self.directory.split(os.sep)[1:])  # remove "log" part of directory

        camera = PiCamera(file_name=video_file_name, directory=video_directory, enabled=True)
        actuators = Actuators(enabled=True)
        sounds = Sounds("sounds", "/home/pi/Music/Bastion/",
                        ("humming", "curiousity", "nothing", "confusion", "concern", "sleepy", "vibrating"),
                        enabled=True)

        cmdline = NaborisCLI()
        website = NaborisWebsite("templates", "static")

        mouse = MouseSensor(enabled=False)

        self.add_nodes(camera, actuators, sounds, cmdline, website, mouse)

        self.subscribe(actuators, cmdline, cmdline.actuators_tag)
        self.subscribe(camera, cmdline, cmdline.capture_tag)
        self.subscribe(sounds, cmdline, cmdline.sounds_tag)

        self.subscribe(cmdline, website, website.cmd_tag)
        self.subscribe(camera, website, website.camera_tag)


run(NaborisOrchestrator)
