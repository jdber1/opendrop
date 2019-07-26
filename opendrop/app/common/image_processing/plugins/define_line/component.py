from typing import Any, Tuple

from gi.repository import Gtk, Gdk

from opendrop.app import keyboard
from opendrop.app.common.image_processing.image_processor import ImageProcessorPluginViewContext
from opendrop.mvp import ComponentSymbol, View, Presenter
from opendrop.utility.bindablegext import GObjectPropertyBindable
from opendrop.utility.geometry import Vector2, Line2
from opendrop.widgets.render.objects import Line
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

        view_context.render.connect(
            'cursor-up-event',
            lambda render, pos: self.presenter.cursor_up(pos),
        )

        view_context.render.connect(
            'cursor-down-event',
            lambda render, pos: self.presenter.cursor_down(pos),
        )

        view_context.render.connect(
            'cursor-motion-event',
            lambda render, pos: self.presenter.cursor_move(pos),
        )

        view_context.render.connect(
            'key-press-event',
            self._hdl_render_key_press_event
        )

        self.bn_tool_button_is_active = self._tool_ref.bn_is_active

        self._render = view_context.render

        self._defined_ro = Line(
            stroke_color=color,
            stroke_width=2,
            draw_control_points=False,
            z_index=z_index,
        )
        self._render.add_render_object(self._defined_ro)

        self._dragging_ro = Line(
            stroke_color=color,
            stroke_width=1,
            draw_control_points=True,
            z_index=z_index,
        )
        self._render.add_render_object(self._dragging_ro)

        self.bn_dragging = GObjectPropertyBindable(
            g_obj=self._dragging_ro,
            prop_name='line',
        )

        self.bn_defined = GObjectPropertyBindable(
            g_obj=self._defined_ro,
            prop_name='line',
        )

        self.presenter.view_ready()

    def _hdl_render_key_press_event(self, widget: Gtk.Widget, event: Gdk.EventKey) -> None:
        self.presenter.key_press(
            keyboard.KeyEvent(
                key=keyboard.Key.from_value(event.keyval),
                modifier=int(event.state)
            )
        )

    def _do_destroy(self) -> None:
        self._render.remove_render_object(self._defined_ro)
        self._render.remove_render_object(self._dragging_ro)


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
            return

        self.view.bn_dragging.set(Line2(
            p0=self._model.begin_define_pos,
            p1=current_cursor_pos,
        ))

    def _do_destroy(self) -> None:
        for db in self.__data_bindings:
            db.unbind()

        for ec in self.__event_connections:
            ec.disconnect()
