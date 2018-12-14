from typing import Generic, TypeVar

from gi.repository import Gtk

T = TypeVar('T', bound=Gtk.Widget)


class GtkWidgetView(Generic[T]):
    # The widget that the view is built upon.
    widget = None  # type: T
