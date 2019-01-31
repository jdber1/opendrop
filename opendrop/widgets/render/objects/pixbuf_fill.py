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

        pixbuf_scaled = self.props.pixbuf.scale_simple(*clip_extents.size, GdkPixbuf.InterpType.BILINEAR)
        Gdk.cairo_set_source_pixbuf(cr, pixbuf_scaled, *clip_extents.pos)

        cr.paint()

    _pixbuf = None  # type: Optional[GdkPixbuf.Pixbuf]

    @GObject.Property
    def pixbuf(self) -> Optional[GdkPixbuf.Pixbuf]:
        return self._pixbuf

    @pixbuf.setter
    def pixbuf(self, value: Optional[GdkPixbuf.Pixbuf]) -> None:
        self._pixbuf = value
        self.emit('request-draw')
