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
    def __init__(self, x_pid, y_pid, th_pid, x_criterion, y_criterion, th_criterion, current_time):
        self.x_pid = x_pid
        self.y_pid = y_pid
        self.th_pid = th_pid

        self.x_criterion = x_criterion
        self.y_criterion = y_criterion
        self.th_criterion = th_criterion

        self.prev_time = current_time

        self.goal_reached = False

    def reset(self, current_time):
        self.prev_time = current_time
        self.goal_reached = False
        self.x_pid.reset()
        self.y_pid.reset()
        self.th_pid.reset()


    def update(self, x_error, y_error, theta_error, current_time):
        dt = current_time - self.prev_time
        self.prev_time = current_time

        strafe_angle = math.atan2(y_error, x_error)

        x_power = self.x_pid.update(math.copysign(x_error * x_error, x_error), dt)
        y_power = self.th_pid.update(math.copysign(y_error * y_error, y_error), dt)
        # command_angular = int(self.th_pid.update(math.copysign(th_error * th_error, th_error), dt))
        command_speed = math.sqrt(x_power * x_power + y_power * y_power)
        command_angle = int(math.degrees(strafe_angle))
        command_angular = 0

        if abs(x_error) < self.x_criterion and abs(y_error) < self.y_criterion: # and abs(theta_error) < self.th_criterion:
            self.goal_reached = True
            return 0, 0, 0

        else:
            return command_speed, command_angle, command_angular
