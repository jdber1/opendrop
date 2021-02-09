from typing import Optional, Sequence

import cairo
from gi.repository import GObject

from opendrop.geometry import Rect2

from ._artist import Artist
from ._util import rectangle_stroke_region


__all__ = ('RectangleArtist',)


class RectangleArtist(Artist):
    _extents: Optional[Rect2[float]] = None
    _stroke_color = (0.0, 0.0, 0.0)
    _stroke_width = 1.0
    _scale_strokes = False

    _last_drawn_region = None
    _last_drawn_stroke_scale = 1.0

    def draw(self, cr: cairo.Context) -> None:
        if self._extents is None:
            return
        
        extents = self._extents
        stroke_color = self._stroke_color
        stroke_width = self._stroke_width

        cr.rectangle(extents.x, extents.y, extents.w, extents.h)

        dx = 1/cr.get_matrix().xx
        dy = 1/cr.get_matrix().yy

        cr.save()

        if self._scale_strokes:
            stroke_scale = max(dx, dy)
            cr.identity_matrix()
        else:
            stroke_scale = 1.0

        cr.set_line_width(stroke_width)
        cr.set_source_rgba(*stroke_color)
        cr.stroke()

        cr.restore()

        self._last_drawn_region = rectangle_stroke_region(extents, max(stroke_width*stroke_scale, dx, dy))
        self._last_drawn_stroke_scale = stroke_scale

    @GObject.Property
    def extents(self) -> Optional[Rect2[float]]:
        return self._extents

    @extents.setter
    def extents(self, extents: Optional[Rect2[float]]) -> None:
        self._extents = extents
        self._invalidate()

    # Style properties

    @GObject.Property(type=bool, default=_scale_strokes)
    def scale_strokes(self) -> bool:
        return self._scale_strokes

    @scale_strokes.setter
    def scale_strokes(self, value: bool) -> None:
        self._scale_strokes = value
        self._invalidate()

    @GObject.Property
    def stroke_color(self) -> Sequence[float]:
        return self._stroke_color

    @stroke_color.setter
    def stroke_color(self, value: Sequence[float]) -> None:
        self._stroke_color = value
        self._invalidate()

    @GObject.Property
    def stroke_width(self) -> float:
        return self._stroke_width

    @stroke_width.setter
    def stroke_width(self, value: float) -> None:
        self._stroke_width = value
        self._invalidate()

    def _invalidate(self) -> None:
        extents = self._extents
        stroke_width = self._stroke_width
        stroke_scale = self._last_drawn_stroke_scale

        inv_region = self._last_drawn_region or cairo.Region()
        inv_region.union(rectangle_stroke_region(extents, stroke_width * stroke_scale))

        self.invalidate(inv_region)
