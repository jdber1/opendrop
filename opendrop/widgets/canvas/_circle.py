from typing import Optional, Sequence
import math

import cairo
from gi.repository import GObject

from opendrop.geometry import Rect2

from ._artist import Artist
from ._util import circle_region


__all__ = ('CircleArtist',)


class CircleArtist(Artist):
    _xc: float = 0.0
    _yc: float = 0.0
    _radius: float = 0.0
    _scale_radius = False
    _fill_color = (0.0, 0.0, 0.0)

    _last_drawn_region: Optional[cairo.Region] = None
    _last_drawn_radius_scale = 1.0

    def draw(self, cr: cairo.Context) -> None:
        xc = self._xc
        yc = self._yc
        radius = self._radius
        scale_radius = self._scale_radius
        fill_color = self._fill_color

        if radius == 0.0:
            return

        matrix = cr.get_matrix()
        dx = 1/matrix.xx
        dy = 1/matrix.yy

        if scale_radius:
            radius_scale = 1/(0.5 * (matrix.xx + matrix.yy))
        else:
            radius_scale = 1.0

        cr.arc(xc, yc, radius_scale*radius, 0, 2*math.pi)
        cr.set_source_rgba(*fill_color)
        cr.fill()

        self._last_drawn_region = circle_region(xc, yc, radius_scale*radius + max(dx, dy))
        self._last_drawn_radius_scale = radius_scale

    @GObject.Property
    def extents(self) -> Optional[Rect2[float]]:
        return self._extents

    @extents.setter
    def extents(self, extents: Optional[Rect2[float]]) -> None:
        self._extents = extents
        self._invalidate()

    @GObject.Property(type=float, default=_xc)
    def xc(self) -> float:
        return self._xc

    @xc.setter
    def xc(self, xc: float) -> None:
        self._xc = xc
        self._invalidate()

    @GObject.Property(type=float, default=_yc)
    def yc(self) -> float:
        return self._yc

    @yc.setter
    def yc(self, yc: float) -> None:
        self._yc = yc
        self._invalidate()

    @GObject.Property(type=float, default=_radius)
    def radius(self) -> float:
        return self._radius

    @radius.setter
    def radius(self, radius: float) -> None:
        self._radius = math.fabs(radius)
        self._invalidate()

    @GObject.Property(type=bool, default=_scale_radius)
    def scale_radius(self) -> bool:
        return self._scale_radius

    @scale_radius.setter
    def scale_radius(self, value: bool) -> None:
        self._scale_radius = value
        self._invalidate()

    @GObject.Property
    def fill_color(self) -> Sequence[float]:
        return self._fill_color

    @fill_color.setter
    def fill_color(self, color: Sequence[float]) -> None:
        self._fill_color = color
        self._invalidate()

    def _invalidate(self) -> None:
        xc = self._xc
        yc = self._yc
        radius = self._radius
        radius_scale = self._last_drawn_radius_scale

        inv_region = self._last_drawn_region or cairo.Region()
        inv_region.union(circle_region(xc, yc, radius_scale*radius))

        self.invalidate(inv_region)
