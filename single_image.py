import os
import cv2
import time
from naboris.masazi.pipeline import MasazIDepthPipeline
from naboris.monodepth.pipeline import MonodepthPipeline
from atlasbuggy import Robot

# file_path = "images/training_data/Screen Shot 2017-07-28 at 11.37.48 AM.png"
# file_path = "images/training_data/rotated Screen Shot 2017-07-28 at 11.41.38 AM.png"
# file_path = "../../obstacle_detection/cnn_depth_tensorflow/data/nyu_datasets/00021.jpg"
# file_path = "../../obstacle_detection/cnn_depth_tensorflow/data/nyu_datasets/00086.jpg"
# file_path = "images/IMG_0715.jpg"
# file_path = "images/Rolls Day ?/IMG_5753.JPG"
# file_path = "images/Sharing/20170422_090847.jpg"
# file_path = "images/Sharing/18110186_1356939561050895_1563625801_o.jpg"
file_path = "images/Sharing/IMG_5996.JPG"

if not os.path.isfile(file_path):
    raise FileNotFoundError(file_path)
image = cv2.imread(file_path)

robot = Robot(write=False)
# depth_pipeline = MasazIDepthPipeline("depth_models/coarse", "depth_models/fine", enabled=True)
depth_pipeline = MonodepthPipeline("kitti_resnet")
depth_pipeline.height, depth_pipeline.width = image.shape[0:2]

t0 = time.time()
depth = depth_pipeline.pipeline(image)
t1 = time.time()

print("took %0.4fs" % (t1 - t0))

cv2.imwrite("output.png", depth)

# cv2.imshow("depth", depth)
# cv2.waitKey(-1)

