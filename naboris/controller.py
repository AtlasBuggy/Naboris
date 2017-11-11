import math


class PID:
    zn_types = {
        "tuning":         (1.0, 0, 0),
        "P":              (0.5, 0, 0),
        "PI":             (0.45, 1 / 1.2, 0),
        "PD":             (0.8, 0, 0.125),
        "PID":            (0.6, 0.5, 0.125),
        "pessen":         (0.7, 0.4, 0.15),
        "some overshoot": (1 / 3, 0.5, 1 / 3),
        "no overshoot":   (0.2, 0.5, 1 / 3)

    }

    def __init__(self, ultimate_gain, ultimate_time_period, ziegler_nichols_type):
        self.reset()

        self.ku = ultimate_gain
        self.tu = ultimate_time_period

        self.select_type(ziegler_nichols_type)
        self.set_ultimate(ultimate_gain, ultimate_time_period)

    def select_type(self, ziegler_nichols_type):
        self.selected_type = PID.zn_types[ziegler_nichols_type]

    def set_ultimate(self, ultimate_gain, ultimate_time_period):
        self.ku = ultimate_gain
        self.tu = ultimate_time_period

        self.kp = self.selected_type[0] * self.ku
        self.ti = self.selected_type[1] * self.tu
        self.td = self.selected_type[2] * self.tu

    def reset(self):
        self.error_sum = 0.0
        self.prev_error = 0.0

    def update(self, error, dt):
        p_term = self.kp * error
        if self.ti:
            i_term = self.kp / self.ti * self.error_sum * dt
        else:
            i_term = 0.0
        d_term = self.kp * self.td * (error - self.prev_error) / dt

        self.prev_error = error
        self.error_sum += error

        return p_term + i_term + d_term


class NaborisController:
    def __init__(self, dist_pid, th_pid, current_time):
        self.dist_pid = dist_pid
        self.th_pid = th_pid

        self.prev_time = current_time

    def update(self, current_state, goal_state, current_time):
        x_c, y_c, theta_c = current_state
        x_g, y_g, theta_g = goal_state
        x_err = x_g - x_c
        y_err = y_g - y_c

        distance_error = math.sqrt(x_err * x_err + y_err * y_err)
        theta_error = theta_g - theta_c

        dt = current_time - self.prev_time
        self.prev_time = current_time

        command_speed = self.dist_pid.update(distance_error, dt)
        command_angular = self.th_pid.update(theta_error, dt)

        return int(command_speed), int(math.degrees(theta_error)), int(command_angular), distance_error, theta_error
