import math
from typing import Callable

from opendrop.app.ift.analysis_model.image_annotator.image_annotator import IFTImageAnnotator
from opendrop.mytypes import Vector2, Rect2


class IFTImageAnnotatorValidator:
    def __init__(self, image_annotator: IFTImageAnnotator,
                 get_image_acquisition_size_hint: Callable[[], Vector2]) -> None:
        self._image_annotator = image_annotator
        self._get_image_acquisition_size_hint = get_image_acquisition_size_hint

    @property
    def is_valid(self) -> bool:
        image_extents = Rect2(pos=(0.0, 0.0), size=self._get_image_acquisition_size_hint())

        drop_region_px = self._image_annotator.bn_drop_region_px.get()
        if drop_region_px is None \
                or drop_region_px.size == (0, 0) \
                or not drop_region_px.is_intersecting(image_extents):
            return False

        needle_region_px = self._image_annotator.bn_needle_region_px.get()
        if needle_region_px is None \
                or needle_region_px.size == (0, 0) \
                or not needle_region_px.is_intersecting(image_extents):
            return False

        needle_width = self._image_annotator.bn_needle_width.get()
        if needle_width is None \
                or needle_width <= 0 \
                or needle_width == 0 \
                or math.isnan(needle_width) \
                or math.isinf(needle_width):
            return False

        return True
