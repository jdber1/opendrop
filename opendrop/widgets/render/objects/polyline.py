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
#E. Huang, T. Denning, A. Skoufis, J. Qi, R. R. Dagastine, R. F. Tabor
#and J. D. Berry, OpenDrop: Open-source software for pendant drop
#tensiometry & contact angle measurements, submitted to the Journal of
# Open Source Software
#
#These citations help us not only to understand who is using and
#developing OpenDrop, and for what purpose, but also to justify
#continued development of this code and other open source resources.
#
# OpenDrop is distributed WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.  You
# should have received a copy of the GNU General Public License along
# with this software.  If not, see <https://www.gnu.org/licenses/>.
import itertools
from typing import Optional, Tuple, Sequence, Union

import cairo
from gi.repository import GObject

from opendrop.utility.cairomisc import cairo_saved
from opendrop.utility.geometry import Vector2
from .. import abc

PolylineType = Sequence[Vector2[float]]


class Polyline(abc.RenderObject):
    _APPROX_MAX_POINTS = 1000

    _polyline = None  # type: Optional[Union[PolylineType, Sequence[PolylineType]]]
    _stroke_color = (0.0, 0.0, 0.0)
    _stroke_width = 1.0  # type: float
    _cache = None

    def draw(self, cr: cairo.Context) -> None:
        polyline = self._polyline
        if polyline is None:
            return

        stroke_width = self.props.stroke_width
        stroke_color = self.props.stroke_color

        with cairo_saved(cr):
            cr.translate(*self._parent._widget_coord_from_canvas((0, 0)))
            cr.scale(*self._parent._widget_dist_from_canvas((1, 1)))

            if self._cache is not None:
                cr.append_path(self._cache)
            else:
                self._draw_paths(cr, polyline)
                self._cache = cr.copy_path()

        cr.set_source_rgb(*stroke_color)
        cr.set_line_width(stroke_width)
        cr.stroke()

    def _draw_paths(self, cr: cairo.Context, polylines: Sequence[PolylineType]) -> None:
        if len(polylines) == 0:
            return

        for polyline in polylines:
            self._draw_path(cr, polyline)

    def _draw_path(self, cr: cairo.Context, polyline: PolylineType) -> None:
        if len(polyline) <= 1:
            return

        if len(polyline) > self._APPROX_MAX_POINTS:
            polyline_reduced = itertools.islice(polyline, 0, None, len(polyline) // self._APPROX_MAX_POINTS)
            polyline = itertools.chain(polyline_reduced, [polyline[-1]])

        points = iter(polyline)

        cr.move_to(*next(points))

        for point in points:
            cr.line_to(*point)

    @GObject.Property
    def polyline(self) -> Optional[Union[PolylineType, Sequence[PolylineType]]]:
        return self._polyline

    @polyline.setter
    def polyline(self, value: Optional[Union[PolylineType, Sequence[PolylineType]]]) -> None:
        self._polyline = value
        self._cache = None
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
