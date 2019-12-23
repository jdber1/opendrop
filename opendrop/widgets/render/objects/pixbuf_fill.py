from typing import Optional

import cairo
from gi.repository import GObject, GdkPixbuf, Gdk

from opendrop.utility.cairomisc import cairo_saved
from .. import abc


class PixbufFill(abc.RenderObject):
    def _do_draw(self, cr: cairo.Context) -> None:
        pixbuf = self.props.pixbuf
        if pixbuf is None:
            return

        scale = self._parent._widget_dist_from_canvas((1, 1))
        offset = self._parent._widget_coord_from_canvas((0, 0))

        with cairo_saved(cr):
            cr.translate(*offset)
            cr.scale(*scale)

            Gdk.cairo_set_source_pixbuf(cr, pixbuf, pixbuf_x=0, pixbuf_y=0)
            cr.get_source().set_filter(cairo.Filter.FAST)
            cr.paint()

    _pixbuf = None  # type: Optional[GdkPixbuf.Pixbuf]

    @GObject.Property
    def pixbuf(self) -> Optional[GdkPixbuf.Pixbuf]:
        return self._pixbuf

    @pixbuf.setter
    def pixbuf(self, value: Optional[GdkPixbuf.Pixbuf]) -> None:
        self._pixbuf = value
        self.emit('request-draw')
