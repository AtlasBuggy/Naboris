import asyncio

from atlasbuggy import Node

from remote.socket_client import NaborisSocketClient


class InceptionCommander(Node):
    def __init__(self, enabled=True):
        super(InceptionCommander, self).__init__(enabled)

        self.pipeline_queue = None
        self.pipeline = None
        self.pipeline_tag = "pipeline"
        self.results_service_tag = "results"
        self.pipeline_sub = self.define_subscription(self.pipeline_tag, service=self.results_service_tag, queue_size=1)

        self.client = None
        self.client_tag = "client"
        self.client_sub = self.define_subscription(self.client_tag, producer_type=NaborisSocketClient, queue_size=None)

        self.good_labels = ["wood", "tile", "carpet"]
        self.bad_labels = ["walllip", "wall", "obstacle"]

    def take(self):
        self.client = self.client_sub.get_producer()
        self.pipeline = self.pipeline_sub.get_producer()
        self.pipeline_queue = self.pipeline_sub.get_queue()

    async def loop(self):
        while True:
            while not self.pipeline_queue.empty():
                prediction_label, prediction_value = await self.pipeline_queue.get()

                if prediction_label in self.good_labels:
                    self.client.send_command("d_0_100")
                    await asyncio.sleep(0.5)
                elif prediction_label in self.bad_labels:
                    self.client.send_command("s")
                    # spin_direction = np.random.choice([150, -150], 1, p=[0.75, 0.25])
                    self.client.send_command("l")
                    # self.client.send_command("look")
                    await asyncio.sleep(1.25)
            await asyncio.sleep(0.01)
