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
    def __init__(self, m_per_px: float, needle_region_px: Rect2[int], drop_region_px: Rect2[int],
                 drop_contour_px: np.ndarray, needle_contours_px: Tuple[np.ndarray, np.ndarray]) -> None:
        # How many metres per pixel.
        self.m_per_px = m_per_px

        self.needle_region_px = needle_region_px
        self.drop_region_px = drop_region_px

        # Coordinates with origin relative to drop_region_px.pos
        self.drop_contour_px = drop_contour_px.copy()
        self.drop_contour_px.flags.writeable = False

        # Coordinates with origin relative to needle_region_px.pos
        self.needle_contours_px = tuple(c.copy() for c in needle_contours_px)
        for c in self.needle_contours_px:
            c.flags.writeable = False
