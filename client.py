from atlasbuggy.opencv import OpenCVViewer
from atlasbuggy import Orchestrator, run

from naboris.inception.pipeline import InceptionPipeline
from naboris.orbslam2.pipeline import OrbslamPipeline
from remote.socket_client import NaborisSocketClient
from remote.inception_commander import InceptionCommander
from remote.orb_commander import OrbCommander

use_orbslam = True
use_inception = False


class ClientOrchestrator(Orchestrator):
    def __init__(self, event_loop):
        self.set_default(level=30)
        super(ClientOrchestrator, self).__init__(event_loop)

        socket = NaborisSocketClient(
            address=("192.168.200.1", 5000),
        )
        inception_pipeline = InceptionPipeline(enabled=use_inception)
        orb_pipeline = OrbslamPipeline("naboris/orbslam2/ORBvoc.txt", "naboris/orbslam2/naboris.yaml",
                                       enabled=use_orbslam, visualize=True)
        viewer = OpenCVViewer(enable_trackbar=False, enabled=use_inception)
        inception_commander = InceptionCommander(enabled=use_inception)
        orb_commander = OrbCommander(
            [(5, 5, 0)], enabled=use_orbslam
        )

        self.add_nodes(socket, orb_pipeline, inception_pipeline, viewer, inception_commander, orb_commander)

        self.subscribe(socket, orb_pipeline, orb_pipeline.capture_tag)
        self.subscribe(socket, orb_commander, orb_commander.client_tag)
        self.subscribe(socket, inception_pipeline, inception_pipeline.capture_tag)
        self.subscribe(socket, inception_commander, inception_commander.client_tag)

        self.subscribe(inception_pipeline, viewer, viewer.capture_tag)
        self.subscribe(inception_pipeline, inception_commander, inception_commander.pipeline_tag)

        self.subscribe(orb_pipeline, orb_commander, orb_commander.pipeline_tag)


run(ClientOrchestrator)
