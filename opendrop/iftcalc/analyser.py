from typing import Tuple

import numpy as np

from opendrop.mytypes import Rect2


class IFTPhysicalParameters:
    def __init__(self, inner_density: float, outer_density: float, needle_width: float, gravity: float) -> None:
        self.inner_density = inner_density
        self.outer_density = outer_density
        self.needle_width = needle_width
        self.gravity = gravity


class IFTImageAnnotations:
    def __init__(self, m_per_px: float, drop_region_px: Rect2[int], drop_contour_px: np.ndarray,
                 needle_contours_px: Tuple[np.ndarray, np.ndarray]) -> None:
        # How many metres per pixel.
        self.m_per_px = m_per_px

        self.drop_region_px = drop_region_px
        self.drop_contour_px = drop_contour_px
        self.needle_contours_px = needle_contours_px
