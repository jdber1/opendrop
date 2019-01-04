from gi.repository import Gtk

from opendrop.component.gtk_widget_view import GtkWidgetView


class MessageTextView(GtkWidgetView[Gtk.Label]):
    def __init__(self, message: str) -> None:
        self.widget = Gtk.Label(message)
        self.widget.show()
