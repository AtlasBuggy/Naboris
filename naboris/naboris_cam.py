from atlasbuggy.camerastream.picamera import PiCamera


class NaborisCam(PiCamera):
    def __init__(self):
        super(NaborisCam, self).__init__("naboris camera")

    def init_camera(self, camera):
        camera.resolution = (320, 240)
        camera.hflip = True
        camera.vflip = True
