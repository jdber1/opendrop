import cv2
from typing import Optional, Tuple

import numpy as np

from opendrop.iftcalc.analyser import IFTImageAnnotations
from opendrop.mytypes import Rect2, Image
from opendrop.utility import mycv
from opendrop.utility.bindable.bindable import AtomicBindableVar, AtomicBindable


def _get_drop_contour(drop_img: Image) -> np.ndarray:
    if len(drop_img.shape) == 2:
        pass  # Do nothing, we need the image to be grayscale
    elif len(drop_img.shape) == 3 and drop_img.shape[-1] == 3:
        drop_img = cv2.cvtColor(drop_img, code=cv2.COLOR_RGB2GRAY)
    else:
        raise ValueError('drop_img must be grayscale or rgb')

    found_contours = mycv.find_contours(drop_img)

    # Assume the drop contour is the longest contour found (mycv.find_contours() returns found contours in descending
    # order of contour length)
    drop_contour = found_contours[0]
    drop_contour = mycv.squish_contour(drop_contour)

    return drop_contour


def _get_needle_contours(needle_img: Image) -> np.ndarray:
    if not len(needle_img.shape) == 2:
        pass  # Do nothing, we need the image to be grayscale
    elif len(needle_img.shape) == 3 and needle_img.shape[-1] == 3:
        needle_img = cv2.cvtColor(needle_img, code=cv2.COLOR_RGB2GRAY)
    else:
        raise ValueError('needle_img must be grayscale or rgb')

    found_contours = mycv.find_contours(needle_img)

    # Assume the needle side-contours are the two longest contours found.
    needle_contours = found_contours[:2]

    return needle_contours


class IFTImageAnnotator:
    def __init__(self) -> None:
        self.bn_canny_min_thresh = AtomicBindableVar(30)  # type: AtomicBindable[int]
        self.bn_canny_max_thresh = AtomicBindableVar(60)  # type: AtomicBindable[int]

        self.bn_drop_region_px = AtomicBindableVar(None)  # type: AtomicBindable[Optional[Rect2]]
        self.bn_needle_region_px = AtomicBindableVar(None)  # type: AtomicBindable[Optional[Rect2]]

        # Physical needle width is used to calculate the image scale.
        self.bn_needle_width = AtomicBindableVar(None)  # type: AtomicBindable[Optional[float]]

    def apply_edge_detection(self, image: Image) -> Image:
        return cv2.Canny(image, self.bn_canny_min_thresh.get(), self.bn_canny_max_thresh.get())

    def get_drop_contour(self, image: Image) -> np.ndarray:
        pass

    def get_needle_contour(self, image: Image) -> Tuple[np.ndarray, np.ndarray]:
        pass

    def annotate_image(self, image: Image) -> IFTImageAnnotations:
        pass
