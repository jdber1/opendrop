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
from typing import Optional

from gi.repository import Gtk, GObject

from opendrop.utility.gmisc import pixbuf_from_array
from opendrop.geometry import Rect2
from opendrop.widgets.render import Render
from opendrop.widgets.render.objects import PixbufFill, Line, Polyline, Angle
from opendrop.appfw import Presenter, component, install
from opendrop.app.conan.analysis import ConanAnalysis


@component(
    template_path='./image.ui',
)
class ConanReportOverviewImagePresenter(Presenter[Gtk.Container]):
    _analysis = None  # type: Optional[ConanAnalysis]
    event_connections = ()

    def after_view_init(self) -> None:
        self.render = Render(visible=True)
        self.host.add(self.render)

        self.background_ro = PixbufFill()
        self.render.add_render_object(self.background_ro)

        self.surface_line_ro = Line(stroke_color=(0.25, 1.0, 0.25))
        self.render.add_render_object(self.surface_line_ro)

        self.drop_contour_ro = Polyline(stroke_color=(0.0, 0.5, 1.0))
        self.render.add_render_object(self.drop_contour_ro)

        self.left_angle_ro = Angle(stroke_color=(1.0, 0.0, 0.5), clockwise=False)
        self.render.add_render_object(self.left_angle_ro)

        self.right_angle_ro = Angle(stroke_color=(1.0, 0.0, 0.5), clockwise=True)
        self.render.add_render_object(self.right_angle_ro)

        self.surface_line_ro.bind_property(
            'line',
            self.left_angle_ro, 'start-angle',
            GObject.BindingFlags.SYNC_CREATE,
            lambda _, line: -math.atan(line.gradient) if line is not None else 0,
        )

        self.surface_line_ro.bind_property(
            'line',
            self.right_angle_ro, 'start-angle',
            GObject.BindingFlags.SYNC_CREATE,
            lambda _, line: math.pi - (math.atan(line.gradient) if line is not None else 0),
        )

    @install
    @GObject.Property
    def analysis(self) -> Optional[ConanAnalysis]:
        return self._analysis

    @analysis.setter
    def analysis(self, analysis: Optional[ConanAnalysis]) -> None:
        for conn in self.event_connections:
            conn.disconnect()
        self.event_connections = ()

        self._analysis = analysis

        if analysis is None:
            return

        self.event_connections = (
            analysis.bn_image.on_changed.connect(self.analysis_changed),
            analysis.bn_left_angle.on_changed.connect(self.analysis_changed),
            analysis.bn_left_point.on_changed.connect(self.analysis_changed),
            analysis.bn_right_angle.on_changed.connect(self.analysis_changed),
            analysis.bn_right_point.on_changed.connect(self.analysis_changed),
            analysis.bn_surface_line.on_changed.connect(self.analysis_changed),
        )

        self.analysis_changed()

    def analysis_changed(self) -> None:
        analysis = self._analysis
        if analysis is None:
            return

        image = analysis.bn_image.get()
        if image is not None:
            self.background_ro.props.pixbuf = pixbuf_from_array(image)
            self.render.props.canvas_size = image.shape[1::-1]
            self.render.viewport_extents = Rect2(position=(0, 0), size=image.shape[1::-1])
        else:
            self.background_ro.props.pixbuf = None

        left_angle = analysis.bn_left_angle.get()
        if left_angle is not None and math.isfinite(left_angle):
            self.left_angle_ro.props.delta_angle = left_angle

        left_point = analysis.bn_left_point.get()
        if left_point is not None:
            self.left_angle_ro.props.vertex_pos = left_point

        right_angle = analysis.bn_right_angle.get()
        if right_angle is not None and math.isfinite(left_angle):
            self.right_angle_ro.props.delta_angle = -right_angle

        right_point = analysis.bn_right_point.get()
        if right_point is not None:
            self.right_angle_ro.props.vertex_pos = right_point

        line = analysis.bn_surface_line.get()
        if line is not None:
            self.surface_line_ro.props.line = line

    def destroy(self, *_) -> None:
        self.analysis = None
