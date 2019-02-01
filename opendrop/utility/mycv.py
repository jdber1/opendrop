# Some computer vision related functions

import cv2
import numpy as np

# cv2.__version__ is a string of format "major.minor.patch"
# convert it to a tuple of int's (major, minor, patch)
CV2_VERSION = tuple(int(v) for v in cv2.__version__.split("."))


def find_contours(image):
    """
        Calls cv2.findContours() on passed image in a way that is compatible with OpenCV 3.x or 2.x
        versions. Passed image is a numpy.array.

        Note, cv2.findContours() will treat non-zero pixels as 1 and zero pixels as 0, so the edges detected will only
        be those on the boundary of pixels with non-zero and zero values.

        Returns a numpy array of the contours in descending arc length order.
    """
    if len(image.shape) > 2:
        raise ValueError('`image` must be a single channel image')

    if CV2_VERSION >= (3, 2, 0):
        # In OpenCV 3.2, cv2.findContours() does not modify the passed image and instead returns the
        # modified image as the first, of the three, return values.
        _, contours, hierarchy = cv2.findContours(image, cv2.RETR_LIST, cv2.CHAIN_APPROX_TC89_KCOS)
    else:
        contours, hierarchy = cv2.findContours(image, cv2.RETR_LIST, cv2.CHAIN_APPROX_TC89_KCOS)

    # Each contour has shape (n, 1, 2) where 'n' is the number of points. Presumably this is so each
    # point is a size 2 column vector, we don't want this so reshape it to a (n, 2)
    contours = [contour.reshape(contour.shape[0], 2) for contour in contours]

    # Sort the contours by arc length, descending order
    contours.sort(key=lambda c: cv2.arcLength(c, False), reverse=True)

    return contours


# todo: add documentation
def squish_contour(contour: np.ndarray) -> np.ndarray:
    contour = contour.copy()

    path_splice = 0
    path = np.arange(len(contour))
    objective = _polyline_l1(contour, idx=range(len(contour)))

    for i in range(-1, -len(contour), -1):
        path_splice_i = path_splice
        path_i = path
        objective_i = objective
        decreasing = False

        for j in range(path_splice, len(contour)):
            path_splice_ij = j
            path_ij = np.concatenate((path[:path_splice_ij], [i], path[path_splice_ij:-1]))
            objective_ij = _polyline_l1(contour, path_ij)

            if objective_ij < objective_i:
                decreasing = True
                path_i = path_ij
                path_splice_i = j
                objective_i = objective_ij
            elif objective_ij > objective_i and decreasing:
                break

        if objective_i < objective:
            path = path_i
            path_splice = path_splice_i
            objective = objective_i
        elif objective_i > objective:
            break

    squished = contour[path]
    squished = _realign_squished_contour(squished)

    return squished


def _polyline_l1(polyline: np.ndarray, idx) -> float:
    diff = np.diff(polyline[idx], axis=0)
    length = np.sum(abs(diff))
    return length


def _realign_squished_contour(curve: np.ndarray) -> np.ndarray:
    dists = np.sum(abs(curve - np.roll(curve, shift=1, axis=0)), axis=1)
    start_idx = dists.argmax()
    return np.roll(curve, shift=-start_idx, axis=0)
