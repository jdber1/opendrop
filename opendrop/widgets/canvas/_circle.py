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
    _fill_color = (0.0, 0.0, 0.0)

    _last_drawn_region: Optional[cairo.Region] = None

    def draw(self, cr: cairo.Context) -> None:
        xc = self._xc
        yc = self._yc
        radius = self._radius
        fill_color = self._fill_color

        if radius == 0.0:
            return

        dx = 1/cr.get_matrix().xx
        dy = 1/cr.get_matrix().yy

        cr.arc(xc, yc, radius, 0, 2*math.pi)
        cr.set_source_rgba(*fill_color)
        cr.fill()

        self._last_drawn_region = circle_region(xc, yc, radius + max(dx, dy))

    @GObject.Property
    def extents(self) -> Optional[Rect2[float]]:
        return self._extents

    @extents.setter
    def extents(self, extents: Optional[Rect2[float]]) -> None:
        self._extents = extents
        self._invalidate()

    # Style properties
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

        inv_region = self._last_drawn_region or cairo.Region()
        inv_region.union(circle_region(xc, yc, radius))

        self.invalidate(inv_region)
