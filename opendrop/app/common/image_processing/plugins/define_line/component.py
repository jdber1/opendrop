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


from typing import Any, Tuple

from gi.repository import Gtk, Gdk

from opendrop.app import keyboard
from opendrop.app.common.image_processing.image_processor import ImageProcessorPluginViewContext
from opendrop.mvp import ComponentSymbol, View, Presenter
from opendrop.utility.bindable.gextension import GObjectPropertyBindable
from opendrop.geometry import Vector2, Line2
from opendrop.widgets.canvas import LineArtist, CircleArtist
from .model import DefineLinePluginModel

define_line_plugin_cs = ComponentSymbol()  # type: ComponentSymbol[None]


@define_line_plugin_cs.view(options=['view_context', 'tool_id', 'color', 'z_index'])
class DefineLinePluginView(View['DefineLinePluginPresenter', None]):
    def _do_init(
            self,
            view_context: ImageProcessorPluginViewContext,
            tool_id: Any,
            color: Tuple[float, float, float],
            z_index: int,
    ) -> None:
        self._view_context = view_context
        self._tool_ref = view_context.get_tool_item(tool_id)

        view_context.canvas.connect(
            'cursor-up',
            lambda canvas, pos: self.presenter.cursor_up(pos),
        )

        view_context.canvas.connect(
            'cursor-down',
            lambda canvas, pos: self.presenter.cursor_down(pos),
        )

        view_context.canvas.connect(
            'cursor-motion',
            lambda canvas, pos: self.presenter.cursor_move(pos),
        )

        view_context.canvas.connect(
            'key-press-event',
            self._hdl_canvas_key_press_event,
        )

        self.bn_tool_button_is_active = self._tool_ref.bn_is_active

        self._canvas = view_context.canvas

        self._defined_artist = LineArtist(
            stroke_color=color,
            stroke_width=1,
            scale_strokes=True,
        )
        self._canvas.add_artist(self._defined_artist, z_index=z_index)

        self._dragging_artist = LineArtist(
            stroke_color=color,
            stroke_width=1,
            scale_strokes=True,
        )
        self._canvas.add_artist(self._dragging_artist, z_index=z_index)

        self._control_point_artist = CircleArtist(
            fill_color=color,
            scale_radius=True,
        )
        self._canvas.add_artist(self._control_point_artist, z_index=z_index)

        self.bn_defined = GObjectPropertyBindable(
            g_obj=self._defined_artist,
            prop_name='line',
        )

        self.bn_dragging = GObjectPropertyBindable(
            g_obj=self._dragging_artist,
            prop_name='line',
        )

        self.presenter.view_ready()

    def show_control_point(self, xc: float, yc: float) -> None:
        self._control_point_artist.props.xc = xc
        self._control_point_artist.props.yc = yc
        self._control_point_artist.props.radius = 2.0

    def hide_control_point(self) -> None:
        self._control_point_artist.props.radius = 0.0

    def _hdl_canvas_key_press_event(self, widget: Gtk.Widget, event: Gdk.EventKey) -> bool:
        self.presenter.key_press(
            keyboard.KeyEvent(
                key=keyboard.Key.from_value(event.keyval),
                modifier=int(event.state)
            )
        )

        # Stop event propagation.
        return True

    def _do_destroy(self) -> None:
        self._canvas.remove_artist(self._defined_artist)
        self._canvas.remove_artist(self._dragging_artist)


@define_line_plugin_cs.presenter(options=['model'])
class DefineLinePluginPresenter(Presenter['DefineLinePluginView']):
    def _do_init(self, model: DefineLinePluginModel) -> None:
        self._model = model
        self.__data_bindings = []
        self.__event_connections = []

    def view_ready(self) -> None:
        self.__data_bindings.extend([
            self._model.bn_line.bind(
                self.view.bn_defined
            ),
        ])

        self.__event_connections.extend([
            self.view.bn_tool_button_is_active.on_changed.connect(
                self._hdl_tool_button_is_active_changed
            ),
        ])

        self._hdl_tool_button_is_active_changed()

    def _hdl_tool_button_is_active_changed(self) -> None:
        if self._model.is_defining and not self.view.bn_tool_button_is_active.get():
            self._model.discard_define()

    def cursor_down(self, pos: Vector2[float]) -> None:
        if not self.view.bn_tool_button_is_active.get():
            return

        if self._model.is_defining:
            self._model.discard_define()

        self._model.begin_define(pos)

        self._update_dragging_indicator(pos)

    def cursor_up(self, pos: Vector2[float]) -> None:
        if not self.view.bn_tool_button_is_active.get():
            return

        if not self._model.is_defining:
            return

        self._model.commit_define(pos)

        self._update_dragging_indicator(pos)

    def cursor_move(self, pos: Vector2[float]) -> None:
        self._update_dragging_indicator(pos)

    def key_press(self, event: keyboard.KeyEvent) -> None:
        if not self.view.bn_tool_button_is_active.get():
            return

        if self._model.is_defining:
            # User is currently using mouse to define
            return

        if event.key is keyboard.Key.Up:
            self._model.nudge_up()
        elif event.key is keyboard.Key.Down:
            self._model.nudge_down()
        elif event.key is keyboard.Key.Left:
            self._model.nudgerot_anticlockwise()
        elif event.key is keyboard.Key.Right:
            self._model.nudgerot_clockwise()

    def _update_dragging_indicator(self, current_cursor_pos: Vector2[float]) -> None:
        if not self._model.is_defining:
            self.view.bn_dragging.set(None)
            self.view.hide_control_point()
            return

        self.view.bn_dragging.set(Line2(
            pt0=self._model.begin_define_pos,
            pt1=current_cursor_pos,
        ))

        self.view.show_control_point(*self._model.begin_define_pos)

    def _do_destroy(self) -> None:
        for db in self.__data_bindings:
            db.unbind()

        for ec in self.__event_connections:
            ec.disconnect()
