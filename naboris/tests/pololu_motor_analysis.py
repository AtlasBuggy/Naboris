import numpy as np
import matplotlib.pyplot as plt

#rated_voltage = float(input('Please enter the rated voltage in Volts : '))
#stall_torque = float(input('Please enter the stall torque in oz-inch : '))
#stall_current = float(input('Please enter the stall current in mA : '))
#freerun_current = float(input('Please enter the free run current in mA : '))
#freerun_speed = float(input('Please enter the free run speed in RPM : '))

#rated_voltage = 6
#stall_torque = 20.86
#stall_current = 650
#freerun_current = 120
#freerun_speed = 130

rated_voltage = 6
stall_torque = 40
stall_current = 1600
freerun_current = 120
freerun_speed = 200

def press(event):
    if event.key == "q":
        plt.close("all")

fig_num = 0
def make_fig():
    global fig_num
    fig = plt.figure(fig_num)
    fig.canvas.mpl_connect('key_press_event', press)
    fig_num += 1
    return fig
    
def plot_motor_curves(motor_name, rated_voltage, stall_torque, stall_current, freerun_current, freerun_speed): 
    resistance = rated_voltage / stall_current

    torque1 = 0
    torque2 = stall_torque  # oz-inch * (1/141.611932278)= N-m;

    current1 = freerun_current
    current2 = stall_current

    speed1 = freerun_speed
    speed2 = 0

    #plt.plot([torque1, torque2], [current1, current2])
    #plt.plot([torque1, torque2], [speed1, speed2])

    samples = 200

    torques = np.linspace(torque1, torque2, samples)
    speed_vs_torque = []
    current_vs_torque = []
    power_vs_torque = []
    efficiency_vs_torque = []

    for torque in torques:
        speed = (speed2 - speed1) / (torque2 - torque1) * (torque - torque1) + speed1
        current = (current2 - current1) / (torque2 - torque1) * (torque - torque1) + current1
        power = speed * torque
        efficiency = power / (current * rated_voltage)
        
        speed_vs_torque.append(speed)
        current_vs_torque.append(current)
        power_vs_torque.append(power)
        efficiency_vs_torque.append(efficiency)

    speed_plot.plot(torques, speed_vs_torque, label=motor_name)
    current_plot.plot(torques, current_vs_torque, label=motor_name)
    power_plot.plot(torques, power_vs_torque, label=motor_name)
    eff_plot.plot(torques, efficiency_vs_torque, label=motor_name)

    speed_plot.set_title("Speed (rpm) vs. torque (oz-in)")
    current_plot.set_title("Current (mA) vs. torque (oz-in)")
    power_plot.set_title("Power vs. torque (oz-in)")
    eff_plot.set_title("Efficiency vs. torque (oz-in)")

fig = make_fig()
speed_plot = fig.add_subplot(2, 2, 1)
current_plot = fig.add_subplot(2, 2, 2)
power_plot = fig.add_subplot(2, 2, 3)
eff_plot = fig.add_subplot(2, 2, 4)

plot_motor_curves("tiny adafruit motor", 6, 20.86, 650, 120, 130)
plot_motor_curves("tiny pololu motor", 6, 40, 1600, 120, 200)
#plot_motor_curves("medium pololu motor", 6, 33, 2400, 250, 290)
#plot_motor_curves("large pololu motor", 12, 84, 5000, 300, 500)
plot_motor_curves("servo city motor", 12, 16.8, 500, 45, 303)

plt.legend(fontsize='x-small', shadow=True, loc=0)

plt.show()
