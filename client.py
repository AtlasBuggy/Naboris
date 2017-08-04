from atlasbuggy.camera.viewer import CameraViewer
from atlasbuggy.robot import Robot
from atlasbuggy.subscriptions import *

from naboris.inception.pipeline import InceptionPipeline
from remote.socket_client import NaborisSocketClient, CLI, Commander


robot = Robot(log_level=10)

socket = NaborisSocketClient(
    address=("naboris", 5000),
)
pipeline = InceptionPipeline(enabled=True)
viewer = CameraViewer(enable_trackbar=False)
cli = CLI(enabled=False)
commander = Commander()

pipeline.subscribe(Update(pipeline.capture_tag, socket))
viewer.subscribe(Update(viewer.capture_tag, pipeline))
cli.subscribe(Subscription(cli.client_tag, socket))
commander.subscribe(Subscription(commander.client_tag, socket))
commander.subscribe(Update(commander.pipeline_tag, pipeline, service=commander.results_service_tag))

robot.run(socket, viewer, pipeline, cli, commander)
