from typing import Optional, Tuple

import cairo
from gi.repository import GdkPixbuf, GObject

from opendrop.utility.geometry import Rect2
from opendrop.widgets.layered_drawing_area.layered_drawing_area import Layer


class RectangleLayer(Layer):
    def __init__(self, **properties) -> None:
        self._extents = None  # type: Optional[Rect2]
        self._border_colour = (0.0, 0.0, 0.0)
        self._border_width = 1.0  # type: float
        super().__init__(**properties)

    def draw(self, cr: cairo.Context) -> None:
        extents = self._extents

        if extents is None:
            return

        cr.rectangle(*extents.pos, *extents.size)
        cr.set_line_width(self._border_width)
        cr.set_source_rgb(*self._border_colour)  # red, green, blue
        cr.stroke()

    @GObject.Property
    def extents(self) -> Optional[GdkPixbuf.Pixbuf]:
        return self._extents

    @extents.setter
    def extents(self, value: Optional[Rect2]) -> None:
        self._extents = value
        self.emit('request-draw')

    @GObject.Property
    def border_colour(self) -> Tuple[float, float, float]:
        return self._border_colour

    @border_colour.setter
    def border_colour(self, value: Tuple[float, float, float]) -> None:
        self._border_colour = value
        self.emit('request-draw')

    @GObject.Property
    def border_width(self) -> float:
        return self._border_width

    @border_width.setter
    def border_width(self, value: float) -> None:
        self._border_width = value
        self.emit('request-draw')


class RectangleWithLabelLayer(RectangleLayer):
    def __init__(self, **properties) -> None:
        self._label = None  # type: Optional[str]
        super().__init__(**properties)

    def draw(self, cr: cairo.Context) -> None:
        super().draw(cr)

        if self._extents is None:
            return

        cr.set_source_rgb(*self._border_colour)
        cr.set_font_size(10)
        cr.move_to(self._extents.x0, self._extents.y1 + 10)
        cr.show_text(self._label)

    @GObject.Property
    def label(self) -> str:
        return self._label

    @label.setter
    def label(self, value: str) -> None:
        self._label = value
        self.emit('request-draw')
