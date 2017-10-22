import os
import argparse

from atlasbuggy import Orchestrator, run

from naboris.soundfiles import Sounds
from naboris.actuators import Actuators
from naboris.picamera import PiCamera
from naboris.cli import NaborisCLI
from naboris.naboris_site import NaborisWebsite
from naboris.texture.pipeline import TexturePipeline

# from naboris.inception.pipeline import InceptionPipeline


parser = argparse.ArgumentParser()
parser.add_argument("-l", "--log", help="disable logging", action="store_false")
parser.add_argument("-d", "--debug", help="enable debug prints", action="store_true")
args = parser.parse_args()

log = args.log


class NaborisOrchestrator(Orchestrator):
    def __init__(self, event_loop):
        self.set_default(write=log)
        super(NaborisOrchestrator, self).__init__(event_loop)

        video_file_name = self.file_name["file_name"][:-3] + "mp4"
        video_directory = "videos/" + os.path.split(self.directory)[-1]

        camera = PiCamera(file_name=video_file_name, directory=video_directory)
        actuators = Actuators()
        sounds = Sounds("sounds", "/home/pi/Music/Bastion/",
                        ("humming", "curiousity", "nothing", "confusion", "concern", "sleepy", "vibrating"))

        cmdline = NaborisCLI()
        website = NaborisWebsite("templates", "static")

        self.add_nodes(camera, actuators, sounds, cmdline, website)

        self.subscribe(cmdline.actuators_tag, actuators, cmdline)
        self.subscribe(cmdline.capture_tag, actuators, camera)

        self.subscribe(website.cmd_tag, cmdline, website)
        self.subscribe(website.camera_tag, camera, website)


run(NaborisOrchestrator)
