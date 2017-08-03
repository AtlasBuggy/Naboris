from atlasbuggy.camera.viewer import CameraViewer
from atlasbuggy.robot import Robot
from atlasbuggy.subscriptions import *

from naboris.inception.pipeline import InceptionPipeline
from remote.socket_client import NaborisSocketClient, CLI


robot = Robot()

socket = NaborisSocketClient()
pipeline = InceptionPipeline()
viewer = CameraViewer(enable_trackbar=False)
cli = CLI()

pipeline.subscribe(Update(pipeline.capture_tag, socket))
viewer.subscribe(Update(viewer.capture_tag, pipeline))
cli.subscribe(Subscription(cli.client_tag, socket))

robot.run(socket, viewer, pipeline, cli)
