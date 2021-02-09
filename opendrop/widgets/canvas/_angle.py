import math
from typing import Tuple

import cairo
from gi.repository import GObject

from ._artist import Artist


__all__ = ('AngleLabelArtist',)


class AngleLabelArtist(Artist):
    _start_angle: float = 0.0
    _delta_angle: float = 0.0
    _clockwise: bool = False

    _arc_radius: float = 0.0
    _start_line_radius: float = 0.0
    _end_line_radius: float = 0.0

    _x: float = 0.0
    _y: float = 0.0

    _stroke_color: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    _stroke_width: float = 1.0

    _text_radius: float = 0.0
    _text_color: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    _font_size: float = 11.0

    _scale_radii: bool = False
    _scale_text: bool = False
    _scale_strokes: bool = False

    def draw(self, cr: cairo.Context) -> None:
        start_angle = self._start_angle
        delta_angle = self._delta_angle
        clockwise = self._clockwise
        arc_radius = self._arc_radius
        start_line_radius = self._start_line_radius
        end_line_radius = self._end_line_radius
        x = self._x
        y = self._y
        stroke_color = self._stroke_color
        stroke_width = self._stroke_width
        text_radius = self._text_radius
        font_size = self._font_size
        text_color = self._text_color
        scale_radii = self._scale_radii
        scale_text = self._scale_text
        scale_strokes = self._scale_strokes

        if not (math.isfinite(start_angle) and math.isfinite(delta_angle)):
            return

        end_angle = start_angle + delta_angle

        matrix = cr.get_matrix()
        if scale_radii:
            radius_scale = 1/(0.5 * (matrix.xx + matrix.yy))
        else:
            radius_scale = 1.0

        self._show_hand(cr, x, y, -start_angle, radius_scale*start_line_radius)
        self._show_hand(cr, x, y, -end_angle, radius_scale*end_line_radius)

        if clockwise:
            cr.arc(x, y, radius_scale*arc_radius, -start_angle, -end_angle)
        else:
            cr.arc_negative(x, y, radius_scale*arc_radius, -start_angle, -end_angle)

        cr.save()
        if scale_strokes:
            cr.identity_matrix()
        cr.set_source_rgba(*stroke_color)
        cr.set_line_width(stroke_width)
        cr.stroke()
        cr.restore()

        half_angle = (start_angle + end_angle) / 2
        cr.move_to(x, y)
        cr.rel_move_to(
            radius_scale*text_radius *  math.cos(half_angle),
            radius_scale*text_radius * -math.sin(half_angle),
        )

        cr.save()

        cr.set_source_rgba(*text_color)
        cr.set_font_size(font_size)

        if scale_text:
            cr.identity_matrix()

        text = '{:.1f}°'.format(math.degrees(math.fabs(delta_angle)))
        text_extents = cr.text_extents(text)

        cr.rel_move_to(-text_extents.x_bearing, -text_extents.y_bearing)
        cr.rel_move_to(-text_extents.width/2, -text_extents.height/2)
        cr.show_text(text)
        cr.fill()

        cr.restore()

    def _show_hand(self, cr: cairo.Context, x: float, y: float, angle: float, radius: float) -> None:
        if radius == 0.0:
            return
        cr.move_to(x, y)
        cr.rel_line_to(radius * math.cos(angle), radius * math.sin(angle))
        cr.new_sub_path()

    @GObject.Property
    def start_angle(self) -> float:
        return self._start_angle

    @start_angle.setter
    def start_angle(self, angle: float) -> None:
        self._start_angle = angle
        self._invalidate()

    @GObject.Property
    def delta_angle(self) -> float:
        return self._delta_angle

    @delta_angle.setter
    def delta_angle(self, angle: float) -> None:
        self._delta_angle = angle
        self._invalidate()

    @GObject.Property
    def clockwise(self) -> bool:
        return self._clockwise

    @clockwise.setter
    def clockwise(self, value: bool) -> None:
        self._clockwise = value
        self._invalidate()

    @GObject.Property
    def stroke_color(self) -> Tuple[float, float, float]:
        return self._stroke_color

    @stroke_color.setter
    def stroke_color(self, value: Tuple[float, float, float]) -> None:
        self._stroke_color = value
        self._invalidate()

    @GObject.Property
    def stroke_width(self) -> float:
        return self._stroke_width

    @stroke_width.setter
    def stroke_width(self, width: float) -> None:
        self._stroke_width = width
        self._invalidate()

    @GObject.Property
    def arc_radius(self) -> float:
        return self._arc_radius

    @arc_radius.setter
    def arc_radius(self, radius: float) -> None:
        self._arc_radius = radius
        self._invalidate()

    @GObject.Property
    def start_line_radius(self) -> float:
        return self._start_line_radius

    @start_line_radius.setter
    def start_line_radius(self, radius: float) -> None:
        self._start_line_radius = radius
        self._invalidate()

    @GObject.Property
    def end_line_radius(self) -> float:
        return self._end_line_radius

    @end_line_radius.setter
    def end_line_radius(self, radius: float) -> None:
        self._end_line_radius = radius
        self._invalidate()

    @GObject.Property
    def x(self) -> float:
        return self._x

    @x.setter
    def x(self, x: float) -> None:
        self._x = x
        self._invalidate()

    @GObject.Property
    def y(self) -> float:
        return self._y

    @y.setter
    def y(self, y: float) -> None:
        self._y = y
        self._invalidate()

    @GObject.Property
    def stroke_color(self) -> Tuple[float, float, float]:
        return self._stroke_color

    @stroke_color.setter
    def stroke_color(self, color: Tuple[float, float, float]) -> None:
        self._stroke_color = color
        self._invalidate()

    @GObject.Property
    def stroke_width(self) -> float:
        return self._stroke_width

    @stroke_width.setter
    def stroke_width(self, width: float) -> None:
        self._stroke_width = width
        self._invalidate()

    @GObject.Property
    def text_radius(self) -> float:
        return self._text_radius

    @text_radius.setter
    def text_radius(self, radius: float) -> None:
        self._text_radius = radius
        self._invalidate()

    @GObject.Property
    def font_size(self) -> float:
        return self._font_size

    @font_size.setter
    def font_size(self, size: float) -> None:
        self._font_size = size
        self._invalidate()

    @GObject.Property
    def text_color(self) -> Tuple[float, float, float]:
        return self._text_color

    @text_color.setter
    def text_color(self, color: Tuple[float, float, float]) -> None:
        self._text_color = color
        self._invalidate()

    @GObject.Property
    def scale_radii(self) -> bool:
        return self._scale_radii

    @scale_radii.setter
    def scale_radii(self, value: bool) -> None:
        self._scale_radii = value
        self._invalidate()

    @GObject.Property
    def scale_text(self) -> bool:
        return self._scale_text

    @scale_text.setter
    def scale_text(self, value: bool) -> None:
        self._scale_text = value
        self._invalidate()

    @GObject.Property
    def scale_strokes(self) -> bool:
        return self._scale_strokes

    @scale_strokes.setter
    def scale_strokes(self, value: bool) -> None:
        self._scale_strokes = value
        self._invalidate()

    def _invalidate(self) -> None:
        self.invalidate()
