import sys
from typing import Optional

import cairo
from gi.repository import GObject, Gdk
import numpy as np

from opendrop.geometry import Rect2

from ._artist import Artist


__all__ = ('ImageArtist',)


class ImageArtist(Artist):
    _extents: Optional[Rect2[float]] = None

    _window: Optional[Gdk.Window] = None
    _surface: Optional[cairo.ImageSurface] = None
    _surface_for_current_window: bool = False
    _last_drawn_region: Optional[cairo.Region] = None

    def map(self, window: Gdk.Window) -> None:
        self._window = window
        self._surface_for_current_window = False

    def unmap(self) -> None:
        self._window = None
        self._surface_for_current_window = False

    def draw(self, cr: cairo.Context) -> None:
        if self._extents is None or self._surface is None:
            return
        
        extents = self._extents
        surface = self._surface

        matrix = cairo.Matrix()
        matrix.scale(surface.get_width()/extents.w, surface.get_height()/extents.h)
        matrix.translate(-extents.x, -extents.y)

        pattern = cairo.SurfacePattern(surface)
        pattern.set_filter(cairo.Filter.FAST)
        pattern.set_matrix(matrix)

        cr.set_source(pattern)
        cr.paint()

        self._last_drawn_region = cairo.Region(cairo.RectangleInt(
            int(extents.x - 1),
            int(extents.y - 1),
            int(extents.w + 2),
            int(extents.h + 2)
        ))

    def set_rgbarray(self, arr: np.ndarray) -> None:
        data = np.pad(arr, pad_width=[(0, 0), (0, 0), (1, 0)], constant_values=0).view(np.uint32)
        if sys.byteorder == 'little':
            data.byteswap(inplace=True)
        width = arr.shape[1]
        height = arr.shape[0]
        self.set_data(data, cairo.Format.RGB24, width, height)

    def set_data(self, data: memoryview, fmt: cairo.Format, width: int, height: int):
        if self._surface is not None and \
                self._surface_for_current_window \
                and self._surface.get_format() == fmt \
                and self._surface.get_width() == width \
                and self._surface.get_height() == height:
            surface = self._surface
        elif self._window is not None:
            surface = Gdk.Window.create_similar_image_surface(
                self._window,
                fmt,
                width,
                height,
                scale=1,
            )
            self._surface_for_current_window = True
        else:
            surface = cairo.ImageSurface(fmt, width, height)
            self._surface_for_current_window = False

        surface.flush()
        surface.get_data()[:] = memoryview(data).cast('B')
        surface.mark_dirty()

        self._surface = surface
        self.invalidate(self._last_drawn_region)

    def clear_data(self) -> None:
        self._surface = None
        self.invalidate(self._last_drawn_region)

    @GObject.Property
    def extents(self) -> Optional[Rect2[float]]:
        return self._extents

    @extents.setter
    def extents(self, extents: Optional[Rect2[float]]) -> None:
        self._extents = extents

        inv_region = self._last_drawn_region

        if extents:
            to_draw = cairo.Region(cairo.RectangleInt(
                int(extents.x - 1),
                int(extents.y - 1),
                int(extents.w + 2),
                int(extents.h + 2)
            ))
            if inv_region is not None:
                inv_region.union(to_draw)
            else:
                inv_region = to_draw

        if inv_region is not None:
            self.invalidate(inv_region)
