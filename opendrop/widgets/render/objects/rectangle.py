from typing import Optional, Tuple

import cairo
from gi.repository import GObject

from opendrop.utility.geometry import Rect2
from .. import abc


class Rectangle(abc.RenderObject):
    def _do_draw(self, cr: cairo.Context) -> None:
        extents = self.props.extents
        border_width = self.props.border_width
        border_color = self.props.border_color

        if extents is None:
            return

        cr.rectangle(*self._parent._widget_coord_from_canvas(extents.pos),
                     *self._parent._widget_dist_from_canvas(extents.size))

        cr.set_line_width(border_width)
        cr.set_source_rgb(*border_color)
        cr.stroke()

    _extents = None  # type: Optional[Rect2[float]]

    @GObject.Property
    def extents(self) -> Optional[Rect2]:
        return self._extents

    @extents.setter
    def extents(self, value: Optional[Rect2]) -> None:
        self._extents = value
        self.emit('request-draw')

    # Style properties

    __border_color = (0.0, 0.0, 0.0)
    __border_width = 1.0

    @GObject.Property
    def border_color(self) -> Tuple[float, float, float]:
        return self.__border_color

    @border_color.setter
    def border_color(self, value: Tuple[float, float, float]) -> None:
        self.__border_color = value
        self.emit('request-draw')

    @GObject.Property
    def border_width(self) -> float:
        return self.__border_width

    @border_width.setter
    def border_width(self, value: float) -> None:
        self.__border_width = value
        self.emit('request-draw')


class RectangleWithLabel(Rectangle):
    def _do_draw(self, cr: cairo.Context) -> None:
        super()._do_draw(cr)

        extents = self.props.extents
        border_color = self.props.border_color
        label = self.props.label

        if extents is None:
            return

        text_pos = self._parent._widget_coord_from_canvas(extents.pos + (0, extents.size.y)) + (0, 10)

        cr.set_source_rgb(*border_color)
        cr.set_font_size(10)
        cr.move_to(*text_pos)
        cr.show_text(label)

    _label = ''

    @GObject.Property
    def label(self) -> str:
        return self._label

    @label.setter
    def label(self, value: str) -> None:
        self._label = value
        self.emit('request-draw')
