import itertools
from typing import Optional, Tuple, Sequence

import cairo
from gi.repository import GObject

from opendrop.utility.cairomisc import cairo_saved
from opendrop.utility.geometry import Vector2
from .. import abc


class Polyline(abc.RenderObject):
    _APPROX_MAX_POINTS = 1000

    _polyline = None  # type: Optional[Sequence[Vector2]]
    _stroke_color = (0.0, 0.0, 0.0)
    _stroke_width = 1.0  # type: float
    _cache = None

    def draw(self, cr: cairo.Context) -> None:
        polyline = self._polyline
        if polyline is None:
            return

        stroke_width = self.props.stroke_width
        stroke_color = self.props.stroke_color

        with cairo_saved(cr):
            cr.translate(*self._parent._widget_coord_from_canvas((0, 0)))
            cr.scale(*self._parent._widget_dist_from_canvas((1, 1)))

            if self._cache is not None:
                cr.append_path(self._cache)
            elif len(polyline) >= 2:
                if len(polyline) > self._APPROX_MAX_POINTS:
                    polyline_reduced = itertools.islice(polyline, 0, None, len(polyline) // self._APPROX_MAX_POINTS)
                    polyline = itertools.chain(polyline_reduced, [polyline[-1]])

                points = iter(polyline) #iter(map(self._parent._widget_coord_from_canvas, polyline))

                cr.move_to(*next(points))

                for point in points:
                    cr.line_to(*point)

                self._cache = cr.copy_path()

        cr.set_source_rgb(*stroke_color)
        cr.set_line_width(stroke_width)
        cr.stroke()

    @GObject.Property
    def polyline(self) -> Optional[Sequence[Vector2[float]]]:
        return self._polyline

    @polyline.setter
    def polyline(self, value: Optional[Sequence[Vector2[float]]]) -> None:
        self._polyline = value
        self._cache = None
        self.emit('request-draw')

    @GObject.Property
    def stroke_color(self) -> Tuple[float, float, float]:
        return self._stroke_color

    @stroke_color.setter
    def stroke_color(self, value: Tuple[float, float, float]) -> None:
        self._stroke_color = value
        self.emit('request-draw')

    @GObject.Property
    def stroke_width(self) -> float:
        return self._stroke_width

    @stroke_width.setter
    def stroke_width(self, value: float) -> None:
        self._stroke_width = value
        self.emit('request-draw')
