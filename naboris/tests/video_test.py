import numpy as np
import time
from atlasbuggy.robot import Robot
from atlasbuggy.camerastream.videoplayer import VideoPlayer
from atlasbuggy.camerastream.cvcamera import CvCamera
from atlasbuggy.uistream.camera_viewer import CameraViewer
from atlasbuggy.uistream.plotters.plot import RobotPlot
from atlasbuggy.uistream.plotters.liveplotter import LivePlotter


with_video = True


def update():
    cam_plot_1.append(time.time() - viewer.start_time, viewer.capture.num_frames)


def update_cam():
    cam_plot_2.append(time.time() - viewer.start_time, len(np.where(capture.frame > 128)[0]))


cam_plot_1 = RobotPlot("cam data 1")
cam_plot_2 = RobotPlot("cam data 2")
plotter = LivePlotter(2, cam_plot_1, cam_plot_2)

if with_video:
    capture = VideoPlayer("00_03_26rightcam.mp4",
                         "/home/pi/Naboris/naboris/")
    viewer = CameraViewer(capture, slider_ticks=capture.slider_ticks)
    capture.link_slider(viewer.slider_name)
else:
    capture = CvCamera(capture_number=0)
    viewer = CameraViewer(capture)

viewer.update = update
capture.update = update_cam

robot = Robot(capture, viewer, plotter)
robot.run()
