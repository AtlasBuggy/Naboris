import sys
import time
import asyncio
import traceback

from atlasbuggy import Node

from naboris.orbslam2.pipeline import OrbslamMessage
from naboris.controller import PID, NaborisController
from remote.socket_client import NaborisSocketClient


class OrbCommander(Node):
    def __init__(self, robot_trajectory, enabled=True, tuning_mode=False):
        super(OrbCommander, self).__init__(enabled)

        self.pipeline_queue = None
        self.pipeline = None
        self.pipeline_tag = "pipeline"
        self.results_service_tag = "results"
        self.pipeline_sub = self.define_subscription(self.pipeline_tag, service=self.results_service_tag, queue_size=1,
                                                     message_type=OrbslamMessage)
        self.pipeline_sub.enabled = False

        self.client = None
        self.client_tag = "client"
        self.client_sub = self.define_subscription(self.client_tag, producer_type=NaborisSocketClient, queue_size=None)

        self.dist_pid = PID(1.0, 0.0, "tuning")
        self.th_pid = PID(1.0, 0.0, "tuning")
        self.controller = NaborisController(self.dist_pid, self.th_pid)
        self.robot_trajectory = robot_trajectory
        self.current_index = 0
        self.enable_pid = False

        self.tuning_mode = tuning_mode
        self.state_data = []

        self.should_exit = False
        self.prompt_text = ">> "
        self.cli_queue = asyncio.Queue()

    async def setup(self):
        self.event_loop.add_reader(sys.stdin, self.handle_stdin)

    def handle_stdin(self):
        data = sys.stdin.readline()
        asyncio.async(self.cli_queue.put(data))

    def handle_input(self, line):
        if line == "start":
            self.dist_pid.reset()
            self.th_pid.reset()
            self.enable_pid = True
            self.pipeline_sub.enabled = True
            self.current_index = 0
            self.logger.info("pid enabled")

        elif line == "stop":
            self.enable_pid = False
            self.pipeline_sub.enabled = False
            self.logger.info("pid disabled. Nothing being commanded")

        elif line[0] == "k":
            self.dist_pid.set_ultimate(float(line[1:]), 0.0)
            print("ku = %s" % self.dist_pid.ku)

        elif line[0:2] == "up":
            self.dist_pid.set_ultimate(self.dist_pid.ku + float(line[2:]), 0.0)
            print("ku = %s" % self.dist_pid.ku)

        elif line[0:2] == "dn":
            self.dist_pid.set_ultimate(self.dist_pid.ku - float(line[2:]), 0.0)
            print("ku = %s" % self.dist_pid.ku)

        elif line == "q":
            self.should_exit = True

    def take(self):
        self.client = self.client_sub.get_producer()
        self.pipeline = self.pipeline_sub.get_producer()
        self.pipeline_queue = self.pipeline_sub.get_queue()

    async def loop(self):
        prev_time = time.time()
        while True:
            if self.enable_pid:
                while not self.pipeline_queue.empty():
                    command = await self.get_command()
                    self.client.send_command(command)
                    await asyncio.sleep(0.01)

                if time.time() - prev_time > 1:
                    self.current_index += 1
                    if self.current_index >= len(self.robot_trajectory):
                        self.current_index = 0
                        self.logger.info("cycling back to goal point 0")
                    self.logger.info("switching to goal #%s" % self.current_index)

            if not self.cli_queue.empty():
                while not self.cli_queue.empty():
                    print("\r%s" % self.prompt_text, end="")
                    data = await self.cli_queue.get()
                    try:
                        self.handle_input(data.strip('\n'))
                    except BaseException as error:
                        traceback.print_exc()
                        print(error)
                        self.logger.warning("Failed to parse input: " + repr(data))

                    if self.should_exit:
                        return

            await asyncio.sleep(0.01)

    async def get_command(self):
        message = await self.pipeline_queue.get()
        roll, pitch, yaw = message.get_euler()
        current = message.x, message.y, yaw
        goal = self.robot_trajectory[self.current_index]

        if self.tuning_mode:
            self.state_data.append(current)

        command_speed, command_angular, command_angle = self.controller.update(current, goal, time.time())
        self.logger.info("sending: speed = %s, angular = %s, angle = %s" % (
            command_speed, command_angular, command_angle))

        return "d_%s_%s_%s" % (command_angle, command_speed, command_angular)

    async def teardown(self):
        if self.tuning_mode:
            path = self.log_file_name + " state data.txt"
            with open(path, 'w') as file:
                for state in self.state_data:
                    file.write("%s\t%s\t%s\n" % state)
            self.logger.info("saved trajectory to %s" % path)
