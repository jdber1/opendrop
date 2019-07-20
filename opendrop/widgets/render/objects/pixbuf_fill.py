from typing import Optional

import cairo
from gi.repository import GObject, GdkPixbuf, Gdk

from opendrop.utility.geometry import Rect2
from .. import abc


class PixbufFill(abc.RenderObject):
    def _do_draw(self, cr: cairo.Context) -> None:
        if self._pixbuf is None:
            return

        clip_extents = cr.clip_extents()
        clip_extents = Rect2(p0=clip_extents[:2], p1=clip_extents[2:])

        if clip_extents.w == 0 or clip_extents.h == 0:
            return

        source_pixbuf = self.props.pixbuf
        cropped_pixbuf = GdkPixbuf.Pixbuf.new(
            colorspace=source_pixbuf.get_colorspace(),
            has_alpha=source_pixbuf.get_has_alpha(),
            bits_per_sample=source_pixbuf.get_bits_per_sample(),
            width=clip_extents.w,
            height=clip_extents.h
        )

        scale = self._parent._widget_dist_from_canvas((1, 1))
        offset = -scale * self._parent._canvas_coord_from_widget(clip_extents.pos)

        self.props.pixbuf.scale(
            cropped_pixbuf,
            0, 0,
            *clip_extents.size,
            *offset,
            *scale,
            GdkPixbuf.InterpType.BILINEAR,
        )

        Gdk.cairo_set_source_pixbuf(cr, cropped_pixbuf, *clip_extents.pos)
        cr.paint()

    _pixbuf = None  # type: Optional[GdkPixbuf.Pixbuf]

    @GObject.Property
    def pixbuf(self) -> Optional[GdkPixbuf.Pixbuf]:
        return self._pixbuf

    @pixbuf.setter
    def pixbuf(self, value: Optional[GdkPixbuf.Pixbuf]) -> None:
        self._pixbuf = value
        self.emit('request-draw')
