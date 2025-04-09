from typing import Optional
import math

import cairo

from opendrop.geometry import Rect2


def rectangle_stroke_region(rect: Optional[Rect2[float]], width: float) -> cairo.Region:
    if rect is None:
        return cairo.Region()

    left_side = cairo.RectangleInt(
        int(math.floor(rect.x0 - width - 1)), int(math.floor(rect.y0 - width - 1)),
        int(math.ceil(2*width + 2)), int(math.ceil(rect.h + 2*width + 2)),
    )

    right_side = cairo.RectangleInt(
        int(math.floor(rect.x1 - width - 1)), int(math.floor(rect.y0 - width - 1)),
        int(math.ceil(2*width + 2)), int(math.ceil(rect.h + 2*width + 2)),
    )

    top_side = cairo.RectangleInt(
        int(math.floor(rect.x0 - width - 1)), int(math.floor(rect.y0 - width - 1)),
        int(math.ceil(rect.w + 2*width + 2)), int(math.ceil(2*width + 2)),
    )

    bottom_side = cairo.RectangleInt(
        int(math.floor(rect.x0 - width - 1)), int(math.floor(rect.y1 - width - 1)),
        int(math.ceil(rect.w + 2*width + 2)), int(math.ceil(2*width + 2)),
    )

    return cairo.Region([left_side, right_side, top_side, bottom_side])


def circle_region(x: float, y: float, radius: float):
    radius = math.fabs(radius)

    if radius == 0.0:
        return cairo.Region()

    return cairo.Region(cairo.RectangleInt(
        x=int(math.floor(x-radius)),
        y=int(math.floor(y-radius)),
        width=int(math.ceil(2*radius)),
        height=int(math.ceil(2*radius)),
    ))


def expand_rect(rect: Rect2[float], size: float):
    return Rect2(
        x0=rect.x0 - size,
        y0=rect.y0 - size,
        x1=rect.x1 + size,
        y1=rect.y1 + size,
    )
