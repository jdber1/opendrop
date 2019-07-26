from typing import Tuple, Optional

import cairo
import numpy as np
from gi.repository import GObject

from opendrop.utility.cairomisc import cairo_saved
from .. import abc


class MaskFill(abc.RenderObject):
    def _do_draw(self, cr: cairo.Context) -> None:
        mask = self._mask
        if mask is None:
            return

        scale = self._parent._widget_dist_from_canvas((1, 1))
        offset = self._parent._widget_coord_from_canvas((0, 0))

        with cairo_saved(cr):
            cr.translate(*offset)
            cr.scale(*scale)

            mask_surface = cairo.ImageSurface.create_for_data(
                memoryview(mask),
                cairo.FORMAT_A8,
                mask.shape[1],
                mask.shape[0],
            )

            cr.set_source_rgba(*self._color)
            cr.mask_surface(mask_surface, 0, 0)

    _mask = None  # type: Optional[np.ndarray]

    @GObject.Property
    def mask(self) -> np.ndarray:
        return self._mask

    @mask.setter
    def mask(self, mask: np.ndarray) -> None:
        self._mask = mask
        self.emit('request-draw')

    _color = (0.0, 0.0, 0.0)

    @GObject.Property
    def color(self) -> Tuple[float, float, float]:
        return self._color

    @color.setter
    def color(self, color: Tuple[float, float, float]) -> None:
        self._color = color
        self.emit('request-draw')
