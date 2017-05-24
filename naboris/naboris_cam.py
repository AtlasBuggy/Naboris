from atlasbuggy.camerastream.picamera import PiCamera


class NaborisCam(PiCamera):
    def __init__(self):
        super(NaborisCam, self).__init__()

    def init_cam(self, cam):
        cam.resolution = (cam.resolution[0] // 2, cam.resolution[1] // 2)
        cam.framerate = 24
        cam.hflip = True
        cam.vflip = True
