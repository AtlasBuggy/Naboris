import cv2
import zbar
import bisect
import numpy as np

from atlasbuggy.opencv import OpenCVPipeline


def blur_edge(img, d=31):
    h, w = img.shape[:2]
    img_pad = cv2.copyMakeBorder(img, d, d, d, d, cv2.BORDER_WRAP)
    img_blur = cv2.GaussianBlur(img_pad, (2 * d + 1, 2 * d + 1), -1)[d:-d, d:-d]
    y, x = np.indices((h, w))
    dist = np.dstack([x, w - x - 1, y, h - y - 1]).min(-1)
    w = np.minimum(np.float32(dist) / d, 1.0)
    return img * w + img_blur * (1 - w)


def motion_kernel(angle, d, sz=65):
    kern = np.ones((1, d), np.float32)
    c, s = np.cos(angle), np.sin(angle)
    A = np.float32([[c, -s, 0], [s, c, 0]])
    sz2 = sz // 2
    A[:, 2] = (sz2, sz2) - np.dot(A[:, :2], ((d - 1) * 0.5, 0))
    kern = cv2.warpAffine(kern, A, (sz, sz), flags=cv2.INTER_CUBIC)
    return kern


def defocus_kernel(d, sz=65):
    kern = np.zeros((sz, sz), np.uint8)
    cv2.circle(kern, (sz, sz), d, 255, -1, cv2.LINE_AA, shift=1)
    kern = np.float32(kern) / 255.0
    return kern


class BarcodePipeline(OpenCVPipeline):
    def __init__(self, camera_matrix, distortion_coeffs, expected_data, expected_size, enabled=True):
        super(BarcodePipeline, self).__init__(enabled)
        self.scanner = zbar.Scanner()

        self.camera_matrix = camera_matrix
        self.distortion_coeffs = distortion_coeffs
        self.expected_data = expected_data
        self.expected_size = expected_size

        self.qr_service = "qr"
        self.define_service(self.qr_service, message_type=tuple)

        self.angle = np.pi
        self.deconvolve_d = 10
        noise_db = 10.0
        self.noise = 10 ** (-0.1 * noise_db)

    def get_contours(self, binary, epsilon=None, num_contours=None, closed=False, num_edges=None, min_perimeter=0):
        binary, contours, hierarchy = cv2.findContours(binary.copy(), cv2.RETR_TREE,
                                                       cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        sig_contours = []
        perimeters = []

        for contour in contours:
            perimeter = cv2.arcLength(contour, closed=closed)
            if perimeter < min_perimeter:
                continue
            index = bisect.bisect(perimeters, perimeter)
            if epsilon is not None:
                approx = cv2.approxPolyDP(contour, epsilon * perimeter, closed)
                if num_edges is not None:
                    if len(approx) != num_edges:
                        continue

                print(len(approx), approx.size, approx)
                sig_contours.insert(index, approx)
            else:
                sig_contours.insert(index, contour)
            perimeters.insert(index, perimeter)

        if num_contours is None:
            return sig_contours, perimeters
        else:
            return sig_contours[-num_contours:], perimeters[-num_contours:]

    def draw_contours(self, image, contours):
        cv2.drawContours(image, contours, -1, (0, 0, 255), 3)

    def pipeline_old(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        # gray = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 51, 0)
        # gray = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(gray, 100, 200, 3)
        # contours, perimeters = self.get_contours(edges, 0.02, closed=True, num_edges=4, min_perimeter=15)
        # self.draw_contours(image, contours)

        return edges

    def pipeline(self, message):
        gray = cv2.cvtColor(message.image, cv2.COLOR_BGR2GRAY)

        # dx = cv2.norm(cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3))
        # dy = cv2.norm(cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3))
        # sum_sq = dx * dx + dy * dy
        # height, width = gray.shape
        # area = height * width
        # blurriness = 1000.0 / (sum_sq / area + 1e-6)
        #
        # self.noise = blurriness ** 4
        # self.deconvolve_d = int(self.noise) + 1
        #
        # img = np.float32(gray) / 255.0
        # IMG = cv2.dft(img, flags=cv2.DFT_COMPLEX_OUTPUT)
        # # IMG = cv2.dft(image, flags=cv2.DFT_COMPLEX_OUTPUT)
        # psf = motion_kernel(self.angle, self.deconvolve_d)
        # psf /= psf.sum()
        # psf_pad = np.zeros_like(img)
        # kh, kw = psf.shape
        # psf_pad[:kh, :kw] = psf
        # PSF = cv2.dft(psf_pad, flags=cv2.DFT_COMPLEX_OUTPUT, nonzeroRows=kh)
        # PSF2 = (PSF ** 2).sum(-1)
        # iPSF = PSF / (PSF2 + self.noise)[..., np.newaxis]
        # RES = cv2.mulSpectrums(IMG, iPSF, 0)
        # res = cv2.idft(RES, flags=cv2.DFT_SCALE | cv2.DFT_REAL_OUTPUT)
        # res = np.roll(res, -kh // 2, 0)
        # res = np.roll(res, -kw // 2, 1)
        #
        # deblurred = np.uint8(res / np.max(res) * 255.0)

        results = self.scanner.scan(gray)

        for result in results:
            print(result.quality, result.data)
            self.broadcast_nowait((result.type, result.data, result.quality, result.position), self.qr_service)

            image_pts = np.array(result.position, np.double)
            pts = np.int32(image_pts.reshape((-1, 1, 2)))

            # image_pts = pts.reshape((-1, 2, 1))

            if result.data == self.expected_data:
                color = (0, 255, 0)

                status, rotation_vector, translation_vector = \
                    cv2.solvePnP(self.expected_size, image_pts, self.camera_matrix, self.distortion_coeffs)
                print(translation_vector.T)
                # end_point2D, jacobian = cv2.projectPoints(
                #     np.array([(0.0, 0.0, 1000.0)]), rotation_vector,
                #     translation_vector, self.camera_matrix, self.distortion_coeffs)
                #
                # p1 = (int(image_pts[0][0]), int(image_pts[0][1]))
                # p2 = (int(end_point2D[0][0][0]), int(end_point2D[0][0][1]))
                #
                # cv2.line(image, p1, p2, (255, 0, 0), 2)

            else:
                print(result.data)
                color = (0, 0, 255)

            cv2.polylines(image, [pts], True, color, 4)

        return image
