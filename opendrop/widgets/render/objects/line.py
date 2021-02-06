# Copyright © 2020, Joseph Berry, Rico Tabor (opendrop.dev@gmail.com)
# OpenDrop is released under the GNU GPL License. You are free to
# modify and distribute the code, but always under the same license
# (i.e. you cannot make commercial derivatives).
#
# If you use this software in your research, please cite the following
# journal articles:
#
# J. D. Berry, M. J. Neeson, R. R. Dagastine, D. Y. C. Chan and
# R. F. Tabor, Measurement of surface and interfacial tension using
# pendant drop tensiometry. Journal of Colloid and Interface Science 454
# (2015) 226–237. https://doi.org/10.1016/j.jcis.2015.05.012
#
# E. Huang, T. Denning, A. Skoufis, J. Qi, R. R. Dagastine, R. F. Tabor
# and J. D. Berry, OpenDrop: Open-source software for pendant drop
# tensiometry & contact angle measurements, submitted to the Journal of
# Open Source Software
#
# These citations help us not only to understand who is using and
# developing OpenDrop, and for what purpose, but also to justify
# continued development of this code and other open source resources.
#
# OpenDrop is distributed WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.  You
# should have received a copy of the GNU General Public License along
# with this software.  If not, see <https://www.gnu.org/licenses/>.


import math
from typing import Optional, Tuple

import cairo
from gi.repository import GObject

from opendrop.geometry import Line2
from opendrop.widgets.render import abc


class Line(abc.RenderObject):
    _stroke_color = (0.0, 0.0, 0.0)
    _stroke_width = 1
    _draw_control_points = False
    _line = None  # type: Optional[Line2]

    def draw(self, cr: cairo.Context) -> None:
        line = self._line
        if line is None:
            return

        viewport_extents = self._parent.props.viewport_extents

        p0 = line.pt0
        p1 = line.pt1

        if p0 == p1:
            return

        start_point = line.eval(x=viewport_extents.x0)
        end_point = line.eval(x=viewport_extents.x1)

        if not viewport_extents.contains(start_point):
            if start_point.y < viewport_extents.y0:
                y_to_eval = viewport_extents.y0
            else:
                y_to_eval = viewport_extents.y1
            start_point = line.eval(y=y_to_eval)

        if not viewport_extents.contains(end_point):
            if end_point.y < viewport_extents.y0:
                y_to_eval = viewport_extents.y0
            else:
                y_to_eval = viewport_extents.y1
            end_point = line.eval(y=y_to_eval)

        p0, p1, start_point, end_point = map(self._parent._widget_coord_from_canvas, (p0, p1, start_point, end_point))

        cr.move_to(*start_point)
        cr.line_to(*end_point)

        stroke_width = self.props.stroke_width
        stroke_color = self.props.stroke_color

        cr.set_line_width(stroke_width)
        cr.set_source_rgb(*stroke_color)  # red, green, blue
        cr.stroke()

        # Draw the control points of the line.
        if self.props.draw_control_points:
            cr.arc(*p0, stroke_width*2, 0, 2*math.pi)
            cr.close_path()
            cr.arc(*p1, stroke_width*2, 0, 2*math.pi)
            cr.close_path()
            cr.fill()

    @GObject.Property
    def line(self) -> Optional[Line2]:
        return self._line

    @line.setter
    def line(self, value: Optional[Line2]) -> None:
        self._line = value
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
    def draw_control_points(self) -> bool:
        return self._draw_control_points

    @draw_control_points.setter
    def draw_control_points(self, value: float) -> None:
        self._draw_control_points = value
        self.emit('request-draw')
