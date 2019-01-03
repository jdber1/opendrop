from enum import Enum
from typing import Tuple, Optional

import cairo
from gi.repository import Gdk, GdkPixbuf, GObject

from opendrop.widgets.layered_drawing_area.layered_drawing_area import Layer
from opendrop.mytypes import Rect2, Vector2


class DrawStyle(Enum):
    FIT = 0
    FILL = 1


def _calculate_draw_size(draw_style: DrawStyle, image_size: Tuple[int, int], target_size: Tuple[int, int])\
        -> Tuple[int, int]:
    target_aspect = target_size[0] / target_size[1]
    image_aspect = image_size[0] / image_size[1]

    if draw_style is DrawStyle.FILL and (target_aspect > image_aspect) \
            or draw_style is DrawStyle.FIT and (target_aspect <= image_aspect):
        scale_factor = target_size[0] / image_size[0]  # type: float
    else:
        scale_factor = target_size[1] / image_size[1]  # type: float

    return round(image_size[0] * scale_factor), round(image_size[1] * scale_factor)


def _calculate_draw_offset_for_centred_image(image_size: Tuple[int, int], target_size: Tuple[int, int]) -> Tuple[int, int]:
    offset = (round(target_size[0]/2 - image_size[0]/2), round(target_size[1]/2 - image_size[1]/2))
    return offset


class PixbufLayer(Layer):
    def __init__(self, **properties) -> None:
        self._last_draw_extents = None  # type: Optional[Rect2]
        self._source_pixbuf = None  # type: Optional[GdkPixbuf.Pixbuf]
        super().__init__(**properties)

    def draw(self, cr: cairo.Context) -> None:
        source_pixbuf = self._source_pixbuf
        draw_extents = None

        if source_pixbuf is not None:
            source_pixbuf_size = source_pixbuf.props.width, source_pixbuf.props.height
            clip_size = cr.clip_extents()[-2:]

            draw_size = _calculate_draw_size(DrawStyle.FIT, source_pixbuf_size, clip_size)
            draw_offset = _calculate_draw_offset_for_centred_image(draw_size, clip_size)
            draw_extents = Rect2(pos=draw_offset, size=draw_size)

            scaled_pixbuf = source_pixbuf.scale_simple(*draw_size, GdkPixbuf.InterpType.BILINEAR)

            Gdk.cairo_set_source_pixbuf(cr, scaled_pixbuf, *draw_offset)
            cr.paint()

        if self._last_draw_extents != draw_extents:
            self._last_draw_extents = draw_extents
            self.notify('last-draw-extents')

    def source_coord_from_draw_coord(self, pos: Vector2) -> Optional[Vector2]:
        x, y = pos

        source_pixbuf = self._source_pixbuf
        draw_extents = self._last_draw_extents  # type: Optional[Rect2]

        if source_pixbuf is None or draw_extents is None:
            return

        source_pixbuf_size = source_pixbuf.props.width, source_pixbuf.props.height

        x_scale = source_pixbuf_size[0] / draw_extents.w
        y_scale = source_pixbuf_size[1] / draw_extents.h

        transformed_x = (x - draw_extents.x0) * x_scale
        transformed_y = (y - draw_extents.y0) * y_scale

        return transformed_x, transformed_y

    def draw_coord_from_source_coord(self, pos: Vector2) -> Optional[Vector2]:
        x, y = pos

        source_pixbuf = self._source_pixbuf
        draw_extents = self._last_draw_extents  # type: Optional[Rect2]

        if source_pixbuf is None or draw_extents is None:
            return

        source_pixbuf_size = source_pixbuf.props.width, source_pixbuf.props.height

        x_scale = draw_extents.w / source_pixbuf_size[0]
        y_scale = draw_extents.h / source_pixbuf_size[1]

        transformed_x = x*x_scale + draw_extents.x0
        transformed_y = y*y_scale + draw_extents.y0

        return transformed_x, transformed_y

    @GObject.Property
    def last_draw_extents(self) -> Optional[Rect2]:
        return self._last_draw_extents

    @GObject.Property
    def source_pixbuf(self) -> Optional[GdkPixbuf.Pixbuf]:
        return self._source_pixbuf

    @source_pixbuf.setter
    def source_pixfbuf(self, value: Optional[GdkPixbuf.Pixbuf]) -> None:
        self._source_pixbuf = value
        self.emit('request-draw')
