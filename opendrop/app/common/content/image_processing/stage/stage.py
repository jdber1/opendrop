from typing import Optional

from gi.repository import Gdk

from opendrop.mytypes import Image
from opendrop.utility import keyboard
from opendrop.utility.events import Event
from opendrop.utility.geometry import Vector2, Rect2
from opendrop.utility.gmisc import pixbuf_from_array
from opendrop.utility.bindable import AccessorBindable, Bindable, BoxBindable
from opendrop.widgets.render import protocol
from opendrop.widgets.render.objects.pixbuf_fill import PixbufFill


class StageView:
    class Cursor:
        def __init__(self) -> None:
            self.on_down = Event()
            self.on_up = Event()

            self.bn_cursor_name = BoxBindable(None)  # type: Bindable[Optional[str]]
            self.bn_pos = BoxBindable(Vector2(0, 0))

    class Keyboard:
        def __init__(self) -> None:
            self.on_key_press = Event()

    def __init__(self, render: protocol.Render) -> None:
        self._render = render

        self._pixbuf_fill = PixbufFill()
        self._render.add_render_object(self._pixbuf_fill)

        self._is_mouse_inside = False

        self.cursor = self.Cursor()
        self.cursor.bn_cursor_name.on_changed.connect(self._update_cursor_appearance)

        self.keyboard = self.Keyboard()

        self.bn_canvas_source = AccessorBindable(setter=self._set_canvas_source)

        self._render.connect('enter-notify-event', self._hdl_render_mouse_cross)
        self._render.connect('leave-notify-event', self._hdl_render_mouse_cross)
        self._render.connect('cursor-down-event', self._hdl_render_cursor_down_event)
        self._render.connect('cursor-up-event', self._hdl_render_cursor_up_event)
        self._render.connect('cursor-motion-event', lambda _, pos: self.cursor.bn_pos.set(pos))

        self._render.connect('key-press-event', self._hdl_render_key_press_event)

    def _hdl_render_cursor_down_event(self, render: protocol.Render, pos: Vector2[float]) -> None:
        self.cursor.bn_pos.set(pos)
        self.cursor.on_down.fire(pos)

    def _hdl_render_cursor_up_event(self, render: protocol.Render, pos: Vector2[float]) -> None:
        self.cursor.bn_pos.set(pos)
        self.cursor.on_up.fire(pos)

    def _hdl_render_mouse_cross(self, widget: protocol.Render, event: Gdk.EventCrossing) -> None:
        if event.type not in (Gdk.EventType.ENTER_NOTIFY, Gdk.EventType.LEAVE_NOTIFY):
            return

        self._is_mouse_inside = event.type is Gdk.EventType.ENTER_NOTIFY

    def _hdl_render_key_press_event(self, widget: protocol.Render, event: Gdk.EventKey) -> None:
        self.keyboard.on_key_press.fire(
            keyboard.KeyEvent(
                key=keyboard.Key.from_value(event.keyval),
                modifier=int(event.state)))

    _is_mouse_inside_value = False

    @property
    def _is_mouse_inside(self) -> bool:
        return self._is_mouse_inside_value

    @_is_mouse_inside.setter
    def _is_mouse_inside(self, value: bool) -> None:
        self._is_mouse_inside_value = value
        self._update_cursor_appearance()

    def _update_cursor_appearance(self) -> None:
        if not self._is_mouse_inside:
            return

        window = self._render.get_window()
        if window is None:
            return

        cursor_name = self.cursor.bn_cursor_name.get()
        if cursor_name is None:
            window.set_cursor(None)
            return

        display = window.get_display()
        if display is None:
            return

        cursor = Gdk.Cursor.new_from_name(display, cursor_name)
        window.set_cursor(cursor)

    def _set_canvas_source(self, image: Optional[Image]) -> None:
        if image is None:
            self._pixbuf_fill.props.pixbuf = None
            return

        image_size = image.shape[1::-1]
        self._render.props.canvas_size = Vector2(*image_size)
        self._render.props.viewport_extents = Rect2(pos=(0, 0), size=image_size)

        self._pixbuf_fill.props.pixbuf = pixbuf_from_array(image)


class StageTool:
    bn_cursor_name = AccessorBindable(lambda: None)  # type: Bindable[Optional[str]]

    def do_cursor_down(self, pos: Vector2[float]) -> None:
        pass

    def do_cursor_up(self, pos: Vector2[float]) -> None:
        pass

    def do_cursor_motion(self, pos: Vector2[float]) -> None:
        pass

    def do_keyboard_key_press(self, event: keyboard.KeyEvent) -> None:
        pass


class StagePresenter:
    def __init__(self, view: StageView) -> None:
        self._view = view

        self.__destroyed = False
        self.__cleanup_tasks = []

        self._active_tool = None  # type: Optional[StageTool]
        self._active_tool_cleanup_tasks = []

        self.bn_canvas_source = self._view.bn_canvas_source

        event_connections = [
            self._view.cursor.on_down.connect(self._hdl_view_cursor_down),
            self._view.cursor.on_up.connect(self._hdl_view_cursor_up),
            self._view.cursor.bn_pos.on_changed.connect(self._hdl_view_cursor_pos_changed),
            self._view.keyboard.on_key_press.connect(self._hdl_view_keyboard_key_press)]
        self.__cleanup_tasks.extend(ec.disconnect for ec in event_connections)

        self.__cleanup_tasks.append(self._remove_current_active_tool)

    def _hdl_view_cursor_down(self, pos: Vector2[float]) -> None:
        if self._active_tool is None:
            return
        self._active_tool.do_cursor_down(pos)

    def _hdl_view_cursor_up(self, pos: Vector2[float]) -> None:
        if self._active_tool is None:
            return

        self._active_tool.do_cursor_up(pos)

    def _hdl_view_cursor_pos_changed(self) -> None:
        if self._active_tool is None:
            return

        self._active_tool.do_cursor_motion(self._view.cursor.bn_pos.get())

    def _hdl_view_keyboard_key_press(self, event: keyboard.KeyEvent) -> None:
        if self._active_tool is None:
            return

        self._active_tool.do_keyboard_key_press(event)

    @property
    def active_tool(self) -> StageTool:
        return self._active_tool

    @active_tool.setter
    def active_tool(self, new_tool: StageTool) -> None:
        self._remove_current_active_tool()

        if new_tool is None:
            return

        self._active_tool = new_tool
        data_bindings = [
            self._active_tool.bn_cursor_name.bind_to(self._view.cursor.bn_cursor_name)]
        self._active_tool_cleanup_tasks.extend(db.unbind for db in data_bindings)

    def _remove_current_active_tool(self) -> None:
        if self._active_tool is None:
            return

        self._active_tool = None
        for f in self._active_tool_cleanup_tasks:
            f()
        self._active_tool_cleanup_tasks = []

        self._view.cursor.bn_cursor_name.set(None)

    def destroy(self) -> None:
        assert not self.__destroyed
        for f in self.__cleanup_tasks:
            f()
        self.__destroyed = True
