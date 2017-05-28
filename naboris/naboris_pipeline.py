import cv2
import numpy as np
from PIL import Image


class NaborisPipeline:
    def __init__(self):
        self.frame = None

    def update(self, frame):
        frame[0:100, 0:100] = np.array([0, 0, 0])
        self.frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return self.frame

    def raw_frame(self):
        return Image.fromarray(self.frame, 'RGB')
