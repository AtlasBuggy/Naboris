import time
import asyncio
import numpy as np
from atlasbuggy import Node
from naboris.controller import *


class State:
    def __init__(self, x=0.0, y=0.0, theta=0.0):
        self.x = x
        self.y = y
        self.theta = theta
        self.compute_H()

    def compute_H(self):
        c = np.cos(self.theta)
        s = np.sin(self.theta)

        self.H = np.matrix([  # homogeneous transform matrix (from robot frame to global frame)
            [c, -s, self.x],
            [s, c, self.y],
            [0, 0, 1]
        ])
        self.H_inv = np.linalg.inv(self.H)

    def to_global_frame(self, x_rframe, y_rframe, theta_rframe):
        return self.transform(self.H, x_rframe, y_rframe, theta_rframe)

    def to_robot_frame(self, x_gframe, y_gframe, theta_gframe):
        return self.transform(self.H_inv, x_gframe, y_gframe, theta_gframe)

    def transform(self, H, x_rframe, y_rframe, theta_rframe):
        point = H * np.matrix([
            [x_rframe],
            [y_rframe],
            [1]
        ])
        global_x = point[0].item()
        global_y = point[1].item()

        vector = H * np.matrix([
            [np.cos(theta_rframe)],
            [np.sin(theta_rframe)],
            [0]
        ])
        global_angle = np.arctan2(vector[1], vector[0]).item()

        return global_x, global_y, global_angle


class Autonomous(Node):
    def __init__(self, enabled=True):
        super(Autonomous, self).__init__(enabled)

        self.global_frame_heading = State()
        self.global_frame_strafe = State()
        self.goal_frame_heading = State()
        self.goal_frame_strafe = State()

        self.goal_available = False
        self.x_pid = PID(0.01, 0.0, "tuning")
        self.y_pid = PID(0.01, 0.0, "tuning")
        self.th_pid = PID(15.0, 0.0, "tuning")
        self.controller = NaborisController(self.x_pid, self.y_pid, self.th_pid, 50.0, 50.0, 0.01, time.time())

        self.actuators_tag = "actuators"
        self.actuators_sub = self.define_subscription(
            self.actuators_tag,
            queue_size=None,
            required_attributes=(
                "commanded_angle",
            ),
            required_methods=(
                "drive",
                "stop_motors",
            )
        )
        self.actuators = None

        self.print_position_output = False
        self.print_bno055_output = False

        self.encoder_tag = "encoder"
        self.encoder_service_tag = "encoder"
        self.encoder_sub = self.define_subscription(self.encoder_tag, self.encoder_service_tag)
        self.encoder_queue = None

        self.bno055_tag = "bno055"
        self.bno055_service_tag = "bno055"
        self.bno055_sub = self.define_subscription(self.bno055_tag, self.bno055_service_tag)
        self.bno055_queue = None

    def take(self):
        self.encoder_queue = self.encoder_sub.get_queue()
        self.bno055_queue = self.bno055_sub.get_queue()
        self.actuators = self.actuators_sub.get_producer()

    async def loop(self):
        while True:
            while not self.encoder_queue.empty():
                encoder_message = await self.encoder_queue.get()
                if encoder_message.delta_theta is not None:
                    strafe_angle = math.radians(self.actuators.commanded_angle)

                    self.global_frame_strafe.theta = (self.global_frame_heading.theta + strafe_angle) % (2 * math.pi)

                    self.global_frame_strafe.x += encoder_message.delta_dist * math.cos(self.global_frame_strafe.theta)
                    self.global_frame_strafe.y += encoder_message.delta_dist * math.sin(self.global_frame_strafe.theta)

                    self.global_frame_heading.x = self.global_frame_strafe.x
                    self.global_frame_heading.y = self.global_frame_strafe.y

                    if self.print_position_output:
                        print("x=%0.4f, y=%0.4f, th=%0.4f" % (
                            self.global_frame_heading.x, self.global_frame_heading.y, self.heading)
                        )
                    self.global_frame_heading.compute_H()
                    self.global_frame_strafe.compute_H()

            while not self.bno055_queue.empty():
                bno055_message = await self.bno055_queue.get()
                self.global_frame_heading.theta = bno055_message.euler.z

                if self.print_bno055_output:
                    print("r=%0.4f, p=%0.4f, y=%0.4f" % bno055_message.euler.get_tuple())

            self.update_controller()
            await asyncio.sleep(0.01)

    def update_controller(self):
        if self.goal_available:
            if self.controller.goal_reached:
                self.actuators.stop_motors()
            else:
                # gx_rframe, gy_rframe, gth_rframe = self.goal_frame_strafe.to_robot_frame()
                x_error, y_error, th_error = self.global_frame_strafe.to_robot_frame(
                    self.goal_frame_strafe.x,
                    self.goal_frame_strafe.y,
                    self.goal_frame_strafe.theta
                )

                print("error:", x_error, y_error, th_error)

                # x_error = gx_rframe - cx_rframe
                # y_error = gy_rframe - cy_rframe
                # th_error = gth_rframe - cth_rframe

                command_speed, command_angle, command_angular = self.controller.update(x_error, y_error, th_error, time.time())

                print("command:", command_speed, command_angle, command_angular)
                self.actuators.drive(command_speed, command_angle, command_angular)

    def set_goal(self, goal_x, goal_y, goal_theta=None):
        self.goal_frame_heading.x = goal_x
        self.goal_frame_heading.y = goal_y

        self.goal_frame_strafe.x = self.goal_frame_heading.x
        self.goal_frame_strafe.y = self.goal_frame_heading.y

        curr_x = self.global_frame_strafe.x
        curr_y = self.global_frame_strafe.y
        self.goal_frame_strafe.theta = np.arctan2(goal_y - curr_y, goal_x - curr_x)

        if goal_theta is None:
            self.goal_frame_heading.theta = self.global_frame_strafe.theta
        else:
            self.goal_frame_heading.theta = goal_theta

        self.goal_frame_heading.compute_H()
        self.goal_frame_strafe.compute_H()

        self.goal_available = True
        self.controller.reset(time.time())
