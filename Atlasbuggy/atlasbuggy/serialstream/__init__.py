import asyncio
import threading
import time
import traceback

import serial.tools.list_ports

from atlasbuggy.datastream import DataStream
from atlasbuggy.serialstream.clock import Clock, CommandPause, RecurringEvent
from atlasbuggy.serialstream.errors import *
from atlasbuggy.serialstream.object import SerialObject
from atlasbuggy.serialstream.port import SerialPort


class SerialStream(DataStream):
    def __init__(self, *serial_objects, enabled=True, logger=None, debug=False, name=None):
        super(SerialStream, self).__init__(enabled, debug, False, True, name)
        self.logger = logger
        self.log = self.logger is not None and self.logger.enabled
        if self.log:
            print("Writing log to:", self.logger.full_path)

        self.objects = {}
        self.ports = {}
        self.callbacks = {}
        self.recurring = []

        self.loops_per_second = 200
        self.loop_delay = 1 / self.loops_per_second
        self.clock = Clock(self.loops_per_second)
        self.object_list = serial_objects

        self.init_objects(self.object_list)

    def link_callback(self, arg, callback_fn):
        """
        :param arg:
        :param callback_fn: function that takes the parameters timestamp and packet
        :return:
        """
        if type(arg) == str and arg in self.objects.keys():
            whoiam = arg
        elif isinstance(arg, SerialObject):
            whoiam = arg.whoiam
        else:
            raise RobotObjectInitializationError("Linked callback input is an invalid whoiam ID or invalid object:",
                                                 repr(arg))
        self.callbacks[whoiam] = callback_fn

    def link_recurring(self, repeat_time, callback_fn, *args, include_event_in_params=False):
        self.recurring.append(RecurringEvent(repeat_time, time.time(), callback_fn, args, include_event_in_params))

    def dt(self):
        if self.start_time is None:
            return 0.0
        else:
            return time.time() - self.start_time

    def init_objects(self, serial_objects):
        for serial_object in serial_objects:
            serial_object.is_live = True
            if isinstance(serial_object, SerialObject):
                self.objects[serial_object.whoiam] = serial_object
            else:
                raise RobotObjectInitializationError(
                    "Object passed is not valid:", repr(serial_object))

    def init_ports(self):
        discovered_ports = []
        for port_address in self.list_ports():
            discovered_ports.append(SerialPort(port_address, self.debug))
        self.debug_print("Discovered ports:", discovered_ports)

        threads = []
        error_messages = []
        for port in discovered_ports:
            config_thread = threading.Thread(target=self.configure_port, args=(port, error_messages))
            threads.append(config_thread)
            config_thread.start()

        for thread in threads:
            thread.join()

        for error_id, message in error_messages:
            if error_id == 0:
                raise RobotSerialPortWhoiamIdTaken(message)
            elif error_id == 1:
                raise RobotSerialPortNotConfiguredError(message)

        if self.ports.keys() != self.objects.keys():
            unassigned_ids = self.objects.keys() - self.ports.keys()
            if len(unassigned_ids) == 1:
                message = "Failed to assign object with ID "
            else:
                message = "Failed to assign objects with IDs "
            raise RobotObjectNotFoundError(message + str(list(unassigned_ids))[1:-1])

        self.validate_ports()

        if self.debug:
            for whoiam in self.ports.keys():
                self.debug_print("[%s] has ID '%s'" % (self.ports[whoiam].address, whoiam))

    def configure_port(self, port, errors):
        """
        Initialize a serial port recognized by pyserial.
        Only devices that are plugged in should be recognized

        :param port_info: an instance of serial.tools.list_ports_common.ListPortInfo
        :param updates_per_second: how often the port should update
        """
        # initialize SerialPort
        port.initialize()

        self.debug_print("whoiam", port.whoiam)

        # check for duplicate IDs
        if port.whoiam in self.ports.keys():
            errors.append((0, "whoiam ID already being used by another port! It's possible "
                              "the same code was uploaded for two boards.\n"
                              "Port address: %s, ID: %s" % (port.address, port.whoiam)))

        # check if port abides protocol. Warn the user and stop the port if not (ignore it essentially)
        elif port.configured and (not port.abides_protocols or port.whoiam is None):
            self.debug_print("Warning! Port '%s' does not abide by protocol!" % port.address)
            port.stop()

        # check if port is configured correctly
        elif not port.configured:
            errors.append((1, "Port not configured! '%s'" % port.address))

        # disable ports if the corresponding object if disabled
        elif not self.objects[port.whoiam].enabled:
            port.stop()
            self.debug_print("Ignoring port with ID: %s (Disabled by user)" % port.whoiam)

        # add the port if configured and abides protocol
        else:
            self.ports[port.whoiam] = port

    def validate_ports(self):
        """
        Validate that all ports are assigned to enabled objects. Warn the user otherwise
            (this allows for ports not listed in objects to be plugged in but not used)
        """
        used_ports = {}
        for whoiam in self.ports.keys():
            if whoiam not in self.objects.keys():
                self.debug_print("Warning! Port ['%s', %s] is unused!" %
                                 (self.ports[whoiam].address, whoiam), ignore_flag=True)
            else:
                # only append port if its used. Ignore it otherwise
                used_ports[whoiam] = self.ports[whoiam]

                # if a robot object signals it wants a different baud rate, change to that rate
                object_baud = self.objects[whoiam].baud
                if object_baud is not None and object_baud != self.ports[whoiam].baud_rate:
                    self.ports[whoiam].change_rate(object_baud)
        self.ports = used_ports

    def list_ports(self):
        ports = list(serial.tools.list_ports.comports())

        port_addresses = []

        # return the port if 'USB' is in the description
        for port_no, description, address in ports:
            if 'USB' in address:
                port_addresses.append(port_no)
        return port_addresses

    def first_packets(self):
        """
        Send each port's first packet to the corresponding object if it isn't an empty string
        """
        status = True
        for whoiam in self.objects.keys():
            first_packet = self.ports[whoiam].first_packet
            if len(first_packet) > 0:
                self.deliver_first_packet(whoiam, first_packet)

                # record first packets
                self.record(None, whoiam, first_packet, "object")
        self.debug_print("First packets sent")

    def deliver_first_packet(self, whoiam, first_packet):
        try:
            if self.objects[whoiam].receive_first(first_packet) is not None:
                self.debug_print("Closing all from first_packets()")
                self.close()
                self.exit()
        except BaseException as error:
            self.close()
            self.exit()
            raise self.handle_error(
                RobotObjectReceiveError(whoiam, first_packet),
                traceback.format_stack()
            )

    def start(self):
        self.clock.start(self.start_time)
        self.init_ports()

        self.first_packets()

        for robot_port in self.ports.values():
            if not robot_port.send_start():
                self.close()
                raise self.handle_error(
                    RobotSerialPortWritePacketError(
                        "Unable to send start packet!", self.timestamp, self.packet, robot_port),
                    traceback.format_stack()
                )

        # start port processes
        for robot_port in self.ports.values():
            robot_port.start()

        self.debug_print("SerialStream is starting")
        try:
            self.serial_start()
        except BaseException as error:
            self.close()
            self.exit()
            raise self.handle_error(error, traceback.format_stack())

    def serial_start(self):
        pass

    async def run(self):
        self.debug_print("SerialStream is running")
        while True:
            for port in self.ports.values():
                self.check_port_packets(port)

            self.update_recurring(time.time())
            self.send_commands()

            # if no packets have been received for a while, update the timestamp with the current clock time
            current_real_time = time.time() - self.start_time
            if self.timestamp is None or current_real_time - self.timestamp > 0.01 or len(self.ports) == 0:
                self.timestamp = current_real_time
            await asyncio.sleep(self.loop_delay)
            # self.clock.update()  # maintain a constant loop speed

    def update_recurring(self, timestamp):
        for event in self.recurring:
            event.update(timestamp)

    def check_port_packets(self, port):
        with port.lock:
            self.check_port_status(port)

            while not port.packet_queue.empty():
                self.timestamp, self.packet = port.packet_queue.get()
                port.counter.value -= 1

                self.deliver(port.whoiam)
                self.received(port.whoiam)

                self.record(self.timestamp, port.whoiam, self.packet, "object")
                self.record_debug_prints(self.timestamp, port)

                port.queue_len = port.counter.value

    def check_port_status(self, port):
        """
        Check if the process is running properly. An error will be thrown if not.

        :return: True if the ports are ok
        """

        status = port.is_running()
        if status < 1:
            self.debug_print("Closing all from check_port_status")
            self.close()
            self.debug_print("status:", status)
            if status == 0:
                raise self.handle_error(
                    RobotSerialPortNotConfiguredError(
                        "Port with ID '%s' isn't configured!" % port.whoiam, self.timestamp, self.packet,
                        port),
                    traceback.format_stack()
                )
            elif status == -1:
                raise self.handle_error(
                    RobotSerialPortSignalledExitError(
                        "Port with ID '%s' signalled to exit" % port.whoiam, self.timestamp, self.packet,
                        port),
                    traceback.format_stack()
                )

    def received(self, whoiam):
        try:
            if whoiam in self.callbacks:
                if self.callbacks[whoiam](self.timestamp, self.packet) is not None:
                    self.debug_print(
                        "callback with whoiam ID: '%s' signalled to exit. Packet: %s" % (
                            whoiam, repr(self.packet)))
                    self.close()
        except BaseException as error:
            self.debug_print("Closing all from received")
            self.close()
            raise self.handle_error(
                PacketReceivedError(error),
                traceback.format_stack()
            )

    def deliver(self, whoiam):
        try:
            if self.objects[whoiam].receive(self.timestamp, self.packet) is not None:
                self.debug_print(
                    "receive for object signalled to exit. whoiam ID: '%s', packet: %s" % (
                        whoiam, repr(self.packet)))
                self.close()

        except BaseException as error:
            self.debug_print("Closing from deliver")
            self.close()
            raise self.handle_error(
                RobotObjectReceiveError(whoiam, self.packet),
                traceback.format_stack()
            )

    def send_commands(self):
        """
        Check every robot object. Send all commands if there are any
        """
        for whoiam in self.objects.keys():
            # loop through all commands and send them
            while not self.objects[whoiam].command_packets.empty():
                if self.objects[whoiam]._pause_command is not None:
                    if self.objects[whoiam]._pause_command.update():
                        self.objects[whoiam]._pause_command = None
                    else:
                        break

                command = self.objects[whoiam].command_packets.get()

                if isinstance(command, CommandPause):
                    self.objects[whoiam]._pause_command = command
                    self.objects[whoiam]._pause_command.prev_time = time.time()
                    self.record(self.timestamp, whoiam, str(command.delay_time), "pause command")
                else:
                    # log sent command.
                    self.record(self.timestamp, whoiam, command, "command")

                    # if write packet fails, throw an error
                    if not self.ports[whoiam].write_packet(command):
                        self.debug_print("Closing all from _send_commands")
                        self.close()
                        raise self.handle_error(
                            RobotSerialPortWritePacketError(
                                "Failed to send command %s to '%s'" % (command, whoiam), self.timestamp, self.packet,
                                self.ports[whoiam]),
                            traceback.format_stack())

    def handle_error(self, error, traceback):
        if self.log:
            error_message = "".join(traceback[:-1])
            error_message += "%s: %s" % (error.__class__.__name__, error.args[0])
            error_message += "\n".join(error.args[1:])
            self.record(self.timestamp, error.__class__.__name__, error_message, "error")

        self.close_log()
        return error

    def close_log(self):
        for port in self.ports.values():
            self.record_debug_prints(self.timestamp, port)
        self.debug_print("Port debug prints recorded")
        self.logger.close()

    def stream_debug_print(self, string):
        self.record(self.timestamp, self.name, string, "debug")

    def record_debug_prints(self, dt, port):
        """
        Take all of the port's queued debug messages and record them
        :param dt: current timestamp
        :param port: RobotSerialPort
        """
        with port.print_out_lock:
            while not port.debug_print_outs.empty():
                self.record(dt, port.whoiam, port.debug_print_outs.get(), "debug")

    def record(self, timestamp, whoiam, packet, packet_type):
        if self.log:
            self.logger.record(timestamp, whoiam, packet, packet_type)

    def stop_all_ports(self):
        """
        Close all robot port processes
        """
        self.debug_print("Closing all ports")

        # stop port processes
        for robot_port in self.ports.values():
            self.debug_print("closing", robot_port.whoiam)
            robot_port.stop()

        for robot_port in self.ports.values():
            self.debug_print("[%s] Port previous packets: read: %s, write %s" % (
                robot_port.whoiam,
                repr(robot_port.prev_read_packets), repr(robot_port.prev_write_packet)))
        time.sleep(0.01)
        # check if the port exited properly
        for port in self.ports.values():
            has_exited = port.has_exited()
            self.debug_print("%s, '%s' has %s" % (port.address, port.whoiam,
                                                  "exited" if has_exited else "not exited!!"))
            if not has_exited:
                raise self.handle_error(RobotSerialPortFailedToStopError(
                    "Port signalled error while stopping", self.timestamp, self.packet,
                    port), traceback.format_stack())
        self.debug_print("All ports exited")

    def close(self):
        """
        Close all SerialPort processes and close their serial ports
        """
        error = None
        try:
            self.serial_close()
        except BaseException as error:
            self.handle_error(error, traceback.format_stack())

        self.send_commands()
        self.debug_print("Sent last commands")
        self.stop_all_ports()
        self.debug_print("Closed ports successfully")
        self.close_log()

        if error is not None:
            self.exit()
            raise error

    def serial_close(self):
        pass
