from typing import Tuple, Optional

import cairo
from gi.repository import GObject

from opendrop.geometry import Line2, Rect2

from ._artist import Artist


__all__ = ('LineArtist',)


class LineArtist(Artist):
    _line: Optional[Line2] = None
    _stroke_color: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    _stroke_width: float = 1.0
    _scale_strokes: bool = False

    def draw(self, cr: cairo.Context) -> None:
        line = self._line
        stroke_color = self._stroke_color
        stroke_width = self._stroke_width
        scale_strokes = self._scale_strokes

        if line is None:
            return

        if line.pt0 == line.pt1:
            return

        clip_extents = Rect2(cr.clip_extents())

        start = line.eval(x=clip_extents.x0)
        end = line.eval(x=clip_extents.x1)

        if not clip_extents.contains(start):
            start = line.eval(y=clip_extents.y0 if start.y < clip_extents.y0 else clip_extents.y1)

        if not clip_extents.contains(end):
            end = line.eval(y=clip_extents.y0 if end.y < clip_extents.y0 else clip_extents.y1)

        cr.move_to(*start)
        cr.line_to(*end)

        cr.save()
        if scale_strokes:
            cr.identity_matrix()
        cr.set_source_rgb(*stroke_color)
        cr.set_line_width(stroke_width)
        cr.stroke()
        cr.restore()

    @GObject.Property
    def line(self) -> Optional[Line2]:
        return self._line

    @line.setter
    def line(self, line: Optional[Line2]) -> None:
        self._line = line
        self._invalidate()

    @GObject.Property
    def stroke_color(self) -> Tuple[float, float, float]:
        return self._stroke_color

    @stroke_color.setter
    def stroke_color(self, color: Tuple[float, float, float]) -> None:
        self._stroke_color = color
        self._invalidate()

    @GObject.Property
    def stroke_width(self) -> float:
        return self._stroke_width

    @stroke_width.setter
    def stroke_width(self, width: float) -> None:
        self._stroke_width = width
        self._invalidate()

    @GObject.Property(type=bool, default=_scale_strokes)
    def scale_strokes(self) -> bool:
        return self._scale_strokes

    @scale_strokes.setter
    def scale_strokes(self, value: bool) -> None:
        self._scale_strokes = value
        self._invalidate()

    def _invalidate(self) -> None:
        self.invalidate()
