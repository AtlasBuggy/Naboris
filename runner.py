import os
import argparse

from atlasbuggy import Orchestrator, run

from naboris.soundfiles import Sounds
from naboris.actuators import Actuators
from naboris.picamera import PiCamera
from naboris.cli import NaborisCLI
from naboris.naboris_site import NaborisWebsite

parser = argparse.ArgumentParser()
parser.add_argument("-l", "--log", help="disable logging", action="store_false")
parser.add_argument("-r", "--record", help="record video at the start", action="store_true")
args = parser.parse_args()

log = args.log
record_video = args.record


class NaborisOrchestrator(Orchestrator):
    def __init__(self, event_loop):
        self.set_default(write=log, level=30)
        super(NaborisOrchestrator, self).__init__(event_loop)

        video_file_name = self.file_name[:-3] + "mp4"
        video_directory = "videos/" + os.path.join(*self.directory.split(os.sep)[1:])  # remove "log" part of directory

        camera = PiCamera(enabled=True, record=record_video, file_name=video_file_name, directory=video_directory)
        actuators = Actuators(enabled=True)

        sounds = Sounds("sounds", "/home/pi/Music/Bastion/",
                        ("humming", "curiousity", "nothing", "confusion", "concern", "sleepy", "vibrating"),
                        enabled=True)

        cmdline = NaborisCLI()
        website = NaborisWebsite("templates", "static")

        self.add_nodes(camera, actuators, sounds, cmdline, website)

        self.subscribe(actuators, cmdline, cmdline.actuators_tag)
        self.subscribe(actuators, cmdline, cmdline.bno055_tag)
        self.subscribe(camera, cmdline, cmdline.capture_tag)
        self.subscribe(sounds, cmdline, cmdline.sounds_tag)

        self.subscribe(cmdline, website, website.cmd_tag)
        self.subscribe(camera, website, website.camera_tag)
        # self.subscribe(actuators, website, website.bno055_tag)


run(NaborisOrchestrator)
