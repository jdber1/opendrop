import math
from typing import Optional, Tuple, Callable, Sequence

import cv2
import numpy as np

from opendrop.app.conan.model.analyser.container import ConanImageAnnotations
from opendrop.mytypes import Image
from opendrop.utility import mycv
from opendrop.utility.geometry import Rect2, Line2
from opendrop.utility.mycv import _realign_squished_contour
from opendrop.utility.simplebindable import Bindable, BoxBindable, apply as bn_apply
from opendrop.utility.validation import validate, check_is_not_empty, check_custom_condition


def _get_drop_contours(drop_img: Image, using_needle: bool) -> Sequence[np.ndarray]:
    IGNORE_EDGE_OVERSCAN = 1

    if len(drop_img.shape) == 2:
        pass  # Do nothing, we need the image to be grayscale
    elif len(drop_img.shape) == 3 and drop_img.shape[-1] == 3:
        drop_img = cv2.cvtColor(drop_img, code=cv2.COLOR_RGB2GRAY)
    else:
        raise ValueError('drop_img must be grayscale or rgb')

    found_contours = mycv.find_contours(drop_img)

    if len(found_contours) == 0:
        return np.empty((0, 2))

    drop_contours = []

    for i in range(2 if using_needle else 1):
        if i >= len(found_contours):
            break

        contour = found_contours[i]
        contour = _realign_squished_contour(contour)

        width, height = drop_img.shape[1::-1]

        if not (width < IGNORE_EDGE_OVERSCAN or height < IGNORE_EDGE_OVERSCAN):
            mask = ((IGNORE_EDGE_OVERSCAN < contour[:, 0]) & (contour[:, 0] < width - IGNORE_EDGE_OVERSCAN) &
                    (IGNORE_EDGE_OVERSCAN < contour[:, 1]) & (contour[:, 1] < height - IGNORE_EDGE_OVERSCAN))
            contour = contour[mask]

        drop_contours.append(contour)

    return drop_contours


class ConanImageAnnotator:
    def __init__(self, get_image_size_hint: Callable[[], Optional[Tuple[int, int]]] = lambda: None) -> None:
        # Used for validation
        self._get_image_size_hint = get_image_size_hint

        self.bn_canny_min = BoxBindable(30)
        self.bn_canny_max = BoxBindable(60)

        self.bn_drop_region_px = BoxBindable(None)  # type: Bindable[Optional[Rect2]]
        self.bn_surface_line_px = BoxBindable(None)  # type: Bindable[Optional[Line2]]

        self.bn_using_needle = BoxBindable(False)

        # Input validation
        self.drop_region_px_err = validate(
            value=self.bn_drop_region_px,
            checks=(check_is_not_empty,
                    check_custom_condition(
                        lambda x: Rect2(pos=(0.0, 0.0), size=self._get_image_size_hint()).is_intersecting(x)
                                  if x is not None and self._get_image_size_hint() is not None else True
                    )))

        self.surface_line_px_err = validate(
            value=self.bn_surface_line_px,
            checks=(check_is_not_empty,))

        self._errors = bn_apply(set.union, self.drop_region_px_err, self.surface_line_px_err)

    def extract_drop_contours(self, image: Image) -> Sequence[np.ndarray]:
        drop_region_px = self.bn_drop_region_px.get()
        if drop_region_px is None:
            return [np.empty((0, 2))]

        drop_region_px = drop_region_px.as_type(int)

        image = image.copy()

        image = self.apply_edge_detection(image)

        drop_image = image[drop_region_px.y0:drop_region_px.y1, drop_region_px.x0:drop_region_px.x1]

        # Set bottom pixels to white (same colour as ground)
        drop_image[-1] = 255

        contours = _get_drop_contours(drop_image, self.bn_using_needle.get())
        contours = tuple(contour + drop_region_px.pos for contour in contours)

        return contours

    def apply_edge_detection(self, image: Image) -> Image:
        # Perform a Gaussian blur first, no way to configure this in the UI currently..
        image = cv2.cvtColor(image, code=cv2.COLOR_RGB2GRAY)
        image = cv2.GaussianBlur(image, (3, 3), 0)
        ret, image = cv2.threshold(image, self.bn_canny_min.get(), self.bn_canny_max.get(), type=cv2.THRESH_BINARY)

        # Rescale to 0-255
        image = cv2.normalize(image, 0, 255, norm_type=cv2.NORM_MINMAX)

        # Make the drop white and the background black
        image = cv2.bitwise_not(image)

        return image

    def _set_pixels_below_surface_to_white(self, image: Image) -> Image:
        line = self.bn_surface_line_px.get()
        if line is None:
            return image

        if not math.isfinite(line.gradient):
            return image

        image = image.copy()
        for x in range(image.shape[1]):
            image[int(line.eval_at(x=x).y):, x] = 255
        return image

    def annotate_image(self, image: Image) -> ConanImageAnnotations:
        drop_region_px = self.bn_drop_region_px.get().as_type(int)
        surface_line_px = self.bn_surface_line_px.get()
        drop_contours_px = self.extract_drop_contours(image)

        return ConanImageAnnotations(
            drop_region_px=drop_region_px,
            surface_line_px=surface_line_px,
            drop_contours_px=drop_contours_px)

    @property
    def has_errors(self) -> bool:
        return bool(self._errors.get())
