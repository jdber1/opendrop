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

import numpy as np
from gi.repository import Gtk, GObject

from opendrop.mvp import ComponentSymbol, View, Presenter
from opendrop.utility.bindable.typing import Bindable
from opendrop.utility.bindable.gextension import GObjectPropertyBindable
from opendrop.utility.geometry import Rect2, Vector2, Line2
from opendrop.utility.gmisc import pixbuf_from_array
from opendrop.widgets.render import Render
from opendrop.widgets.render.objects import PixbufFill, Line, Polyline, Angle

info_cs = ComponentSymbol()  # type: ComponentSymbol[Gtk.Widget]


@info_cs.view()
class InfoView(View['InfoPresenter', Gtk.Widget]):
    def _do_init(self) -> Gtk.Widget:
        self._render = Render(hexpand=True, vexpand=True)

        self._background_ro = PixbufFill()
        self._render.add_render_object(self._background_ro)

        surface_line_ro = Line(stroke_color=(0.25, 1.0, 0.25))
        self._render.add_render_object(surface_line_ro)
        self.bn_surface_line = GObjectPropertyBindable(surface_line_ro, 'line')

        drop_contour_ro = Polyline(stroke_color=(0.0, 0.5, 1.0))
        self._render.add_render_object(drop_contour_ro)
        self.bn_drop_contours = GObjectPropertyBindable(drop_contour_ro, 'polyline')

        left_angle_ro = Angle(stroke_color=(1.0, 0.0, 0.5), clockwise=False)
        self._render.add_render_object(left_angle_ro)

        self.bn_left_angle = GObjectPropertyBindable(left_angle_ro, 'delta-angle')
        self.bn_left_point = GObjectPropertyBindable(left_angle_ro, 'vertex-pos')

        surface_line_ro.bind_property(
            'line',
            left_angle_ro, 'start-angle',
            GObject.BindingFlags.SYNC_CREATE,
            lambda _, line: -math.atan(line.gradient) if line is not None else 0
        )

        right_angle_ro = Angle(stroke_color=(1.0, 0.0, 0.5), clockwise=True)
        self._render.add_render_object(right_angle_ro)

        self.bn_right_angle = GObjectPropertyBindable(
            right_angle_ro, 'delta-angle',
            transform_to=lambda angle: -angle,
            transform_from=lambda angle: -angle
        )
        self.bn_right_point = GObjectPropertyBindable(right_angle_ro, 'vertex-pos')

        surface_line_ro.bind_property(
            'line',
            right_angle_ro, 'start-angle',
            GObject.BindingFlags.SYNC_CREATE,
            lambda _, line: math.pi - (math.atan(line.gradient) if line is not None else 0)
        )

        self.presenter.view_ready()

        return self._render

    def set_background_image(self, image: np.ndarray) -> None:
        if image is None:
            self._background_ro.props.pixbuf = None
            return

        self._background_ro.props.pixbuf = pixbuf_from_array(image)

        self._render.props.canvas_size = image.shape[1::-1]
        self._render.viewport_extents = Rect2(pos=(0, 0), size=image.shape[1::-1])

    def _do_destroy(self) -> None:
        self._render.destroy()


@info_cs.presenter(
    options=[
        'in_image',
        'in_left_angle',
        'in_left_point',
        'in_right_angle',
        'in_right_point',
        'in_surface_line',
    ]
)
class InfoPresenter(Presenter['InfoView']):
    def _do_init(
            self,
            in_image: Bindable[Optional[np.ndarray]],
            in_left_angle: Bindable[float],
            in_left_point: Bindable[Optional[Vector2]],
            in_right_angle: Bindable[float],
            in_right_point: Bindable[Optional[Vector2]],
            in_surface_line: Bindable[Optional[Line2]],
    ) -> None:
        self._bn_image = in_image
        self._bn_left_angle = in_left_angle
        self._bn_left_point = in_left_point
        self._bn_right_angle = in_right_angle
        self._bn_right_point = in_right_point
        self._bn_surface_line = in_surface_line

        self.__data_bindings = []
        self.__event_connections = []

    def view_ready(self):
        self.__data_bindings.extend([
            self._bn_left_angle.bind(
                self.view.bn_left_angle
            ),
            self._bn_left_point.bind(
                self.view.bn_left_point
            ),
            self._bn_right_angle.bind(
                self.view.bn_right_angle
            ),
            self._bn_right_point.bind(
                self.view.bn_right_point
            ),
            self._bn_surface_line.bind(
                self.view.bn_surface_line
            ),
        ])

        self.__event_connections.extend([
            self._bn_image.on_changed.connect(
                self._hdl_image_changed
            ),
        ])

        self._hdl_image_changed()

    def _hdl_image_changed(self) -> None:
        image = self._bn_image.get()
        self.view.set_background_image(image)

    def _do_destroy(self) -> None:
        for db in self.__data_bindings:
            db.unbind()

        for ec in self.__event_connections:
            ec.disconnect()
