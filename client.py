from atlasbuggy.opencv import OpenCVViewer
from atlasbuggy import Orchestrator, run

from naboris.inception.pipeline import InceptionPipeline
from naboris.orbslam2.pipeline import OrbslamPipeline
from remote.socket_client import NaborisSocketClient, InceptionCommander


class ClientOrchestrator(Orchestrator):
    def __init__(self, event_loop):
        self.set_default(level=30)
        super(ClientOrchestrator, self).__init__(event_loop)

        socket = NaborisSocketClient(
            address=("192.168.200.1", 5000),
        )
        # pipeline = InceptionPipeline(enabled=True)
        pipeline = OrbslamPipeline("naboris/orbslam2/ORBvoc.txt", "naboris/orbslam2/naboris.yaml", visualize=True)
        viewer = OpenCVViewer(enable_trackbar=False, enabled=False)
        commander = InceptionCommander(enabled=False)

        self.add_nodes(socket, pipeline, viewer, commander)

        self.subscribe(socket, pipeline, pipeline.capture_tag)
        self.subscribe(socket, commander, commander.client_tag)

        self.subscribe(pipeline, viewer, viewer.capture_tag)
        self.subscribe(pipeline, commander, commander.pipeline_tag)


run(ClientOrchestrator)
