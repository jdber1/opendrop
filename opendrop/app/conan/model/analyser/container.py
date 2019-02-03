from typing import Sequence

import numpy as np

from opendrop.utility.geometry import Rect2, Line2


class ConanImageAnnotations:
    def __init__(self, drop_region_px: Rect2[int], surface_line_px: Line2, drop_contours_px: Sequence[np.ndarray])\
            -> None:
        self.drop_region_px = drop_region_px
        self.surface_line_px = surface_line_px

        # Coordinates with origin relative to image
        self.drop_contours_px = np.copy(drop_contours_px)
        self.drop_contours_px.flags.writeable = False
