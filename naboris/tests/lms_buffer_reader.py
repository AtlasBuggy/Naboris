import numpy as np
import asyncio
from atlasbuggy.ui.plotters.liveplotter import LivePlotter
from atlasbuggy.ui.plotters.plot import RobotPlot
from atlasbuggy.robot import Robot

with open("../buffer2.txt", 'rb') as buffer_file:
    contents = buffer_file.read()


def lms200_crc(data):
    crc16 = 0
    byte = [0, 0]
    for c in data:
        byte[1] = byte[0]
        byte[0] = c

        if crc16 & 0x8000:
            crc16 = (crc16 & 0x7FFF) << 1
            crc16 ^= 0x8005
        else:
            crc16 = crc16 << 1

        crc16 ^= (byte[1] << 8) | byte[0]

    return crc16


index = 0
command = b''
num_commands = 0


def read(n):
    global index, command
    result = contents[index: index + n]
    index += n
    command += result
    if len(result) == 0:
        result = '\x00'
    return result


def parse_16bit(lower_byte, upper_byte):
    return (upper_byte << 8) + lower_byte


async def run(robot):
    global index, command, num_commands
    while index < len(contents):
        char_num = read(1)
        if char_num == b'\x02':
            print("-----")
            if read(1) == b'\x80':
                print("response")
                length = parse_16bit(ord(read(1)), ord(read(1)))
                print("length:", length)

                payload = read(length)
                response = payload[0]
                data = payload[1:]
                print("response: %s, data: %s" % (hex(response), data))
                checksum = parse_16bit(ord(read(1)), ord(read(1)))
                calc_checksum = lms200_crc(command[:-2])

                print("command checksum:", checksum)
                print("calculated checksum:", calc_checksum)
                if calc_checksum != checksum:
                    print("!!invalid checksum!!")

                command = b''

                if response == 0xA0:
                    print("power on response")
                elif response == 0xB0:
                    sample_info = parse_16bit(data[0], data[1])
                    num_samples = sample_info & 0x3ff

                    unit_info_1 = sample_info >> 14 & 1
                    unit_info_2 = sample_info >> 15 & 1
                    if not unit_info_1 and not unit_info_2:
                        units = "cm"
                    elif unit_info_1 and not unit_info_2:
                        units = "mm"
                    else:
                        units = "Reserved"
                    print("units:", units)

                    scan_info = sample_info >> 13 & 1
                    is_complete_scan = not bool(scan_info)
                    print("complete scan:", is_complete_scan)

                    resolution_info_1 = sample_info >> 11 & 1
                    resolution_info_2 = sample_info >> 12 & 1

                    if not resolution_info_1 and not resolution_info_2:
                        resolution = 0
                    elif resolution_info_1 and not resolution_info_2:
                        resolution = 0.25
                    elif not resolution_info_1 and resolution_info_2:
                        resolution = 0.5
                    else:
                        resolution = 0.75
                    print("resolution: %sº" % resolution)

                    distances = []
                    angles = np.linspace(0, np.pi, int(num_samples / 2))
                    for sample_index in range(0, num_samples, 2):
                        distances.append(parse_16bit(data[sample_index], data[sample_index + 1]))

                    distances = np.array(distances)

                    scan_plot.update(distances * np.cos(angles), distances * np.sin(angles))
                    await asyncio.sleep(0.5)

                    print(num_commands)
                    if num_commands > 2:
                        plotter.active_window_resizing = False
                        scan_plot.window_resizing = False
                    num_commands += 1
    plotter.plot()
    # robot.exit()


scan_plot = RobotPlot("lms200", marker='.', linestyle='')
plotter = LivePlotter(1, scan_plot)
Robot.run(plotter, loop_fn=run)
