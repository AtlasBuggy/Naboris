
class Robot:
    def __init__(self, *streams):
        """
        :param robot_objects: instances of atlasbuggy.robot.object.RobotObject or
            atlasbuggy.robot.object.RobotObjectCollection
        """
        self.streams = streams

    def start(self):
        """
        Events to be run when the interface starts (receive_first has been for all enabled robot objects)
        :return: None if ok, "error", "exit", or "done" if the program should exit
        """
        for stream in self.streams:
            stream.start()

    def update(self):
        """
        Events to be run on a loop
        :return: None if ok, "error", "exit", or "done" if the program should exit
        """
        for stream in self.streams:
            stream.update()

    def close(self, reason):
        """
        Events to be run when the interface closes
        :param reason: "error", "exit", or "done"
            error - an error was thrown
            exit - something requested an premature exit
            done - something signalled to the program is done
        """
        for stream in self.streams:
            stream.close()
