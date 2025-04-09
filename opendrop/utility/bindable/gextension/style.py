import weakref
from typing import Any

from gi.repository import Gtk

from opendrop.utility.bindable.abc import Bindable


class GStyleContextClassBindable(Bindable[Any]):
    def __init__(self, style_context: Gtk.StyleContext, class_name: str) -> None:
        super().__init__()

        self._alive = True

        # See GObjectPropertyBindable for an explanation (note that Gtk.StyleContext is a GObject)
        self._style_context = style_context
        self._style_context_wr = weakref.ref(style_context)

        self._class_name = class_name

        self._hdl_style_context_changed_id = self._style_context.connect('changed', self._hdl_style_context_changed)

    def _hdl_style_context_changed(self, style_context: Gtk.StyleContext) -> None:
        if not self._alive:
            return

        self.on_changed.fire()

    def _get_value(self) -> Any:
        assert self._alive

        return self._style_context.has_class(self._class_name)

    def _set_value(self, new_value: Any) -> None:
        assert self._alive

        self._style_context.handler_block(self._hdl_style_context_changed_id)

        try:
            if bool(new_value):
                self._style_context.add_class(self._class_name)
            else:
                self._style_context.remove_class(self._class_name)
        finally:
            self._style_context.handler_unblock(self._hdl_style_context_changed_id)

    def _unlink(self, *_):
        if not self._alive:
            return

        if not self._is_style_context_garbage_collected \
                and self._style_context.handler_is_connected(self._hdl_style_context_changed_id):
            self._style_context.disconnect(self._hdl_style_context_changed_id)

        self._alive = False

    @property
    def _is_style_context_garbage_collected(self) -> bool:
        return self._style_context_wr() is None

    def __del__(self):
        self._unlink()


class GWidgetStyleClassBindable(GStyleContextClassBindable):
    def __init__(self, widget: Gtk.Widget, style_class_name: str) -> None:
        super().__init__(widget.get_style_context(), style_class_name)
