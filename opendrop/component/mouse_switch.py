from typing import Optional, MutableSequence

from gi.repository import Gtk, Gdk

from opendrop.utility.simplebindable import Bindable, BoxBindable
from opendrop.utility.events import EventConnection
from opendrop.utility.geometry import Vector2


class MouseSwitchTarget:
    def __init__(self) -> None:
        self.bn_cursor_name = BoxBindable(None)  # type: Bindable[Optional[str]]

    @property
    def cursor_name(self) -> Optional[str]:
        return self.bn_cursor_name.get()

    @cursor_name.setter
    def cursor_name(self, new_name: Optional[str]) -> None:
        self.bn_cursor_name.set(new_name)

    def do_mouse_move(self, coord: Vector2) -> None:
        """Invoked when mouse is moved"""

    def do_mouse_button_press(self, coord: Vector2) -> None:
        """Invoked when any mouse button is pressed"""

    def do_mouse_button_release(self, coord: Vector2) -> None:
        """Invoked when any mouse button is released"""


class MouseSwitch:
    def __init__(self, event_source: Gtk.Widget) -> None:
        self._event_source = event_source
        self._event_source.connect('enter-notify-event', self._hdl_event_source_enter_or_leave_notify_event)
        self._event_source.connect('leave-notify-event', self._hdl_event_source_enter_or_leave_notify_event)
        self._event_source.connect('button-press-event', self._hdl_event_source_button_press_or_release_event)
        self._event_source.connect('button-release-event', self._hdl_event_source_button_press_or_release_event)
        self._event_source.connect('motion-notify-event', self._hdl_event_source_motion_notify_event)

        self._is_mouse_inside = False
        self._target = None  # type: Optional[MouseSwitchTarget]
        self._target_event_connections = []  # type: MutableSequence[EventConnection]

    @property
    def target(self) -> MouseSwitchTarget:
        return self._target

    @target.setter
    def target(self, new_target: MouseSwitchTarget) -> None:
        for ec in self._target_event_connections:
            ec.disconnect()

        self._target = new_target
        self._target_event_connections = []

        if self._target is not None:
            self._target_event_connections = [
                self._target.bn_cursor_name.on_changed.connect(self._update_cursor_icon)
            ]

        self._update_cursor_icon()

    def _update_cursor_icon(self) -> None:
        if not self._is_mouse_inside:
            return

        window = self._event_source.get_window()
        if window is None:
            return

        target = self.target
        cursor_name = target.cursor_name if target is not None else None
        if cursor_name is None:
            window.set_cursor(None)
            return

        display = window.get_display()
        if display is None:
            return

        cursor = Gdk.Cursor.new_from_name(display, cursor_name)
        window.set_cursor(cursor)

    def _hdl_event_source_enter_or_leave_notify_event(self, event_source: Gtk.Widget, event: Gdk.EventCrossing) -> None:
        if event.type not in (Gdk.EventType.ENTER_NOTIFY, Gdk.EventType.LEAVE_NOTIFY):
            return

        if event.type is Gdk.EventType.ENTER_NOTIFY:
            self._is_mouse_inside = True
        else:
            self._is_mouse_inside = False

        self._update_cursor_icon()

    def _hdl_event_source_button_press_or_release_event(self, event_source: Gtk.Widget, event: Gdk.EventButton) -> None:
        target = self._target
        if target is None:
            return

        if event.type == Gdk.EventType.BUTTON_PRESS:
            target.do_mouse_button_press(Vector2(event.x, event.y))
        elif event.type == Gdk.EventType.BUTTON_RELEASE:
            target.do_mouse_button_release(Vector2(event.x, event.y))

    def _hdl_event_source_motion_notify_event(self, event_source: Gtk.Widget, event: Gdk.EventMotion) -> None:
        target = self._target
        if target is None:
            return

        target.do_mouse_move(Vector2(event.x, event.y))
