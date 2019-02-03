import math
from typing import Tuple

import cairo
from gi.repository import GObject

from opendrop.utility.geometry import Vector2
from opendrop.widgets.render import abc


class Angle(abc.RenderObject):
    _start_angle = 0
    _delta_angle = 0

    _stroke_color = (0.0, 0.0, 0.0)
    _stroke_width = 1

    _angle_radius = 20
    _start_marker_radius = 0
    _end_marker_radius = 50
    _text_radius = 40

    _text_font_size = 11

    _vertex_pos = None

    _clockwise = False

    def draw(self, cr: cairo.Context) -> None:
        vertex_pos = self._vertex_pos
        if vertex_pos is None:
            return

        vertex_pos = self._parent._widget_coord_from_canvas(vertex_pos)
        start_angle = -self._start_angle
        delta_angle = -self._delta_angle
        end_angle = start_angle + delta_angle

        if not (math.isfinite(start_angle) and math.isfinite(end_angle)):
            return

        stroke_width = self._stroke_width
        stroke_color = self._stroke_color
        cr.set_line_width(stroke_width)
        cr.set_source_rgb(*stroke_color)

        # Start marker path
        start_marker_radius = self._start_marker_radius
        self._append_hand_path(cr, vertex_pos, start_angle, start_marker_radius)

        # End marker path
        end_marker_radius = self._end_marker_radius
        self._append_hand_path(cr, vertex_pos, end_angle, end_marker_radius)

        cr.stroke()

        # Angle arc path
        angle_radius = self._angle_radius
        if self._clockwise:
            which_arc = cr.arc
        else:
            which_arc = cr.arc_negative
        which_arc(*vertex_pos, angle_radius, start_angle, end_angle)

        cr.stroke()

        # Text
        mid_angle = (start_angle + end_angle) / 2
        text_radius = self._text_radius
        text_font_size = self._text_font_size
        cr.move_to(*vertex_pos)
        cr.rel_move_to(text_radius * math.cos(mid_angle), text_radius * math.sin(mid_angle))

        cr.set_font_size(text_font_size)
        cr.set_source_rgb(*stroke_color)

        angle_text = '{:.4g}°'.format(math.degrees(abs(delta_angle)))

        text_extents = cr.text_extents(angle_text)
        cr.rel_move_to(-text_extents.x_bearing, -text_extents.y_bearing)
        cr.rel_move_to(-text_extents.width/2, -text_extents.height/2)

        cr.show_text(angle_text)

    def _append_hand_path(self, cr: cairo.Context, pos: Vector2[float], angle: float, radius: float) -> None:
        if radius == 0:
            return

        cr.move_to(*pos)
        cr.rel_line_to(radius * math.cos(angle), radius * math.sin(angle))

    @GObject.Property
    def start_angle(self) -> float:
        return self._start_angle

    @start_angle.setter
    def start_angle(self, value: float) -> None:
        self._start_angle = value
        self.emit('request-draw')

    @GObject.Property
    def delta_angle(self) -> float:
        return self._delta_angle

    @delta_angle.setter
    def delta_angle(self, value: float) -> None:
        self._delta_angle = value
        self.emit('request-draw')

    @GObject.Property
    def clockwise(self) -> bool:
        return self._clockwise

    @clockwise.setter
    def clockwise(self, value: bool) -> None:
        self._clockwise = value
        self.emit('request-draw')

    @GObject.Property
    def stroke_color(self) -> Tuple[float, float, float]:
        return self._stroke_color

    @stroke_color.setter
    def stroke_color(self, value: Tuple[float, float, float]) -> None:
        self._stroke_color = value
        self.emit('request-draw')

    @GObject.Property
    def stroke_width(self) -> float:
        return self._stroke_width

    @stroke_width.setter
    def stroke_width(self, value: float) -> None:
        self._stroke_width = value
        self.emit('request-draw')

    @GObject.Property
    def vertex_pos(self) -> Vector2[float]:
        return self._vertex_pos

    @vertex_pos.setter
    def vertex_pos(self, value: Vector2[float]) -> None:
        self._vertex_pos = value
        self.emit('request-draw')
