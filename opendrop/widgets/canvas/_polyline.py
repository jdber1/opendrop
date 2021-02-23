import math
from typing import Sequence, Tuple, Union, Optional

import cairo
import cv2
from gi.repository import GObject
import numpy as np

from opendrop.geometry import Rect2

from ._artist import Artist
from ._util import expand_rect


__all__ = ('PolylineArtist',)


_PointSequence = Sequence[Tuple[float, float]]


class PolylineArtist(Artist):
    _polyline: Optional[_PointSequence] = None
    _stroke_color: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    _stroke_width: float = 1.0
    _scale_strokes: bool = False

    _path_cache = None
    _last_drawn_region: Optional[cairo.Region] = None

    def draw(self, cr: cairo.Context) -> None:
        polyline = self._polyline
        stroke_width = self._stroke_width
        stroke_color = self._stroke_color

        if polyline is None or len(polyline) == 0:
            self._last_drawn_region = None
            return

        if self._path_cache is not None:
            cr.append_path(self._path_cache)
        else:
            self._show_polyline(cr, polyline)
            self._path_cache = cr.copy_path()
        extents = Rect2(cr.path_extents())

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

        extents = expand_rect(extents, max(stroke_width*stroke_scale, dx, dy))
        self._last_drawn_region = cairo.Region(cairo.RectangleInt(
            int(math.floor(extents.x)),
            int(math.floor(extents.y)),
            int(math.ceil(extents.w)),
            int(math.ceil(extents.h)),
        ))

    def _show_polyline(self, cr: cairo.Context, polyline: _PointSequence) -> None:
        if len(polyline) <= 1:
            return

        polyline = cv2.approxPolyDP(
            np.asarray(polyline, dtype=np.float32),
            epsilon=1.0,
            closed=False
        ).reshape(-1, 2)

        points_it = iter(polyline)
        cr.move_to(*next(points_it))

        for point in points_it:
            cr.line_to(*point)

    @GObject.Property
    def polyline(self) -> Union[_PointSequence, Sequence[_PointSequence], None]:
        return self._polyline

    @polyline.setter
    def polyline(self, polyline: Union[_PointSequence, Sequence[_PointSequence], None]) -> None:
        self._polyline = polyline
        self._path_cache = None
        self._invalidate()

    @GObject.Property
    def stroke_color(self) -> Tuple[float, float, float]:
        return self._stroke_color

    @stroke_color.setter
    def stroke_color(self, value: Tuple[float, float, float]) -> None:
        self._stroke_color = value
        self._invalidate_last_drawn()

    @GObject.Property
    def stroke_width(self) -> float:
        return self._stroke_width

    @stroke_width.setter
    def stroke_width(self, value: float) -> None:
        self._stroke_width = value
        self._invalidate()

    @GObject.Property(type=bool, default=_scale_strokes)
    def scale_strokes(self) -> bool:
        return self._scale_strokes

    @scale_strokes.setter
    def scale_strokes(self, value: bool) -> None:
        self._scale_strokes = value
        self._invalidate()

    def _invalidate_last_drawn(self) -> None:
        self.invalidate(self._last_drawn_region)

    def _invalidate(self) -> None:
        self.invalidate()
