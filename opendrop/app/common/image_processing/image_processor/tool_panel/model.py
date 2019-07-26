from typing import Optional, Any, Callable

from gi.repository import Gtk

from opendrop.utility.bindable import Bindable
from opendrop.utility.bindablegext import GObjectPropertyBindable


class ToolItemRef:
    def __init__(self) -> None:
        self._referents_set = False

        self._bn_is_active = None  # type: Optional[Bindable[bool]]
        self._tool_button = None  # type: Optional[Gtk.Button]
        self._tool_button_interior = None  # type: Optional[Gtk.Grid]

    def set_referents(
            self,
            tool_id: Any,
            tool_button: Gtk.Button,
            tool_button_interior: Gtk.Grid,
            do_request_deactivate: Callable[[Any], Any],
    ) -> None:
        assert not self._referents_set
        self._referents_set = True

        self._bn_is_active = GObjectPropertyBindable(
            g_obj=tool_button,
            prop_name='active',
        )

        self._tool_id = tool_id
        self._tool_button = tool_button
        self._tool_button_interior = tool_button_interior
        self._do_request_deactivate = do_request_deactivate

    @property
    def bn_is_active(self) -> Bindable[bool]:
        assert self._bn_is_active is not None
        return self._bn_is_active

    @property
    def button_interior(self) -> Gtk.Grid:
        assert self._tool_button_interior is not None
        return self._tool_button_interior

    @property
    def button_window(self) -> Optional[Gtk.Window]:
        assert self._tool_button is not None
        toplevel = self._tool_button.get_toplevel()
        if isinstance(toplevel, Gtk.Window):
            return toplevel
        else:
            return None

    def request_deactivate(self) -> None:
        self._do_request_deactivate(self._tool_id)
