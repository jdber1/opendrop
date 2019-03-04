from typing import Optional, Tuple, Callable

import cv2
import numpy as np

from opendrop.app.ift.model.analyser import IFTImageAnnotations
from opendrop.mytypes import Image
from opendrop.utility import mycv
from opendrop.utility.bindable import bindable_function
from opendrop.utility.bindable.bindable import AtomicBindableVar, AtomicBindable
from opendrop.utility.geometry import Rect2
from opendrop.utility.validation import validate, check_is_positive, check_is_not_empty, check_custom_condition
from .needle_width import get_needle_width_from_contours


def _get_drop_contour(drop_img: Image) -> np.ndarray:
    if len(drop_img.shape) == 2:
        pass  # Do nothing, we need the image to be grayscale
    elif len(drop_img.shape) == 3 and drop_img.shape[-1] == 3:
        drop_img = cv2.cvtColor(drop_img, code=cv2.COLOR_RGB2GRAY)
    else:
        raise ValueError('drop_img must be grayscale or rgb')

    found_contours = mycv.find_contours(drop_img)

    if len(found_contours) == 0:
        return np.empty((0, 2))

    # Assume the drop contour is the longest contour found (mycv.find_contours() returns found contours in descending
    # order of contour length)
    drop_contour = found_contours[0]
    drop_contour = mycv.squish_contour(drop_contour)

    return drop_contour


def _get_needle_contours(needle_img: Image) -> Tuple[np.ndarray, np.ndarray]:
    if len(needle_img.shape) == 2:
        pass  # Do nothing, we need the image to be grayscale
    elif len(needle_img.shape) == 3 and needle_img.shape[-1] == 3:
        needle_img = cv2.cvtColor(needle_img, code=cv2.COLOR_RGB2GRAY)
    else:
        raise ValueError('needle_img must be grayscale or rgb')

    found_contours = mycv.find_contours(needle_img)

    # Assume the needle side-contours are the two longest contours found.
    needle_contours = tuple(found_contours[:2])

    return needle_contours


class IFTImageAnnotator:
    def __init__(self, get_image_size_hint: Callable[[], Optional[Tuple[int, int]]] = lambda: None) -> None:
        # Used for validation
        self._get_image_size_hint = get_image_size_hint

        self.bn_canny_min = AtomicBindableVar(30)  # type: AtomicBindable[int]
        self.bn_canny_max = AtomicBindableVar(60)  # type: AtomicBindable[int]

        self.bn_drop_region_px = AtomicBindableVar(None)  # type: AtomicBindable[Optional[Rect2]]
        self.bn_needle_region_px = AtomicBindableVar(None)  # type: AtomicBindable[Optional[Rect2]]

        # Physical needle width (in metres) is used to calculate the image scale.
        self.bn_needle_width = AtomicBindableVar(None)  # type: AtomicBindable[Optional[float]]

        # Input validation
        self.drop_region_px_err = validate(
            value=self.bn_drop_region_px,
            checks=(check_is_not_empty,
                    check_custom_condition(
                        lambda x: Rect2(pos=(0.0, 0.0), size=self._get_image_size_hint()).is_intersecting(x)
                                  if x is not None and self._get_image_size_hint() is not None else True
                    )))

        self.needle_region_px_err = validate(
            value=self.bn_needle_region_px,
            checks=(check_is_not_empty,
                    check_custom_condition(
                        lambda x: Rect2(pos=(0.0, 0.0), size=self._get_image_size_hint()).is_intersecting(x)
                                  if x is not None and self._get_image_size_hint() is not None else True
                    )))

        self.needle_width_err = validate(
            value=self.bn_needle_width,
            checks=(check_is_positive, check_is_not_empty))

        self._errors = bindable_function(set.union)(
            self.drop_region_px_err, self.needle_region_px_err, self.needle_width_err)(AtomicBindableVar(True))

    def extract_drop_contour(self, image: Image) -> np.ndarray:
        drop_region_px = self.bn_drop_region_px.get()
        if drop_region_px is None:
            return np.empty((0, 2))
        drop_region_px = drop_region_px.as_type(int)

        image = self.apply_edge_detection(image)
        drop_image = image[drop_region_px.y0:drop_region_px.y1, drop_region_px.x0:drop_region_px.x1]

        contour = _get_drop_contour(drop_image)
        contour += drop_region_px.pos

        return contour

    def apply_edge_detection(self, image: Image) -> Image:
        # Perform a Gaussian blur first, no way to configure this in the UI currently..
        image = cv2.GaussianBlur(image, (3, 3), 0)

        return cv2.Canny(image, self.bn_canny_min.get(), self.bn_canny_max.get())

    def annotate_image(self, image: Image) -> IFTImageAnnotations:
        image = self.apply_edge_detection(image)

        drop_region_px = self.bn_drop_region_px.get()
        needle_region_px = self.bn_needle_region_px.get()

        drop_region_px = drop_region_px.as_type(int)
        needle_region_px = needle_region_px.as_type(int)

        drop_image = image[drop_region_px.y0:drop_region_px.y1, drop_region_px.x0:drop_region_px.x1]
        needle_image = image[needle_region_px.y0:needle_region_px.y1, needle_region_px.x0:needle_region_px.x1]

        drop_contour_px = _get_drop_contour(drop_image)
        drop_contour_px += drop_region_px.pos

        needle_contours_px = _get_needle_contours(needle_image)
        needle_contours_px = tuple(contour + needle_region_px.pos for contour in needle_contours_px)  # type: Tuple[np.ndarray, np.ndarray]

        needle_width_px = get_needle_width_from_contours(needle_contours_px)
        needle_width = self.bn_needle_width.get()
        m_per_px = needle_width/needle_width_px

        return IFTImageAnnotations(
            m_per_px=m_per_px,
            needle_region_px=needle_region_px,
            drop_region_px=drop_region_px,
            drop_contour_px=drop_contour_px,
            needle_contours_px=needle_contours_px
        )

    @property
    def has_errors(self) -> bool:
        return bool(self._errors.get())
