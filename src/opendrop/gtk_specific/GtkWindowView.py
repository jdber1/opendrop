from typing import Optional

from gi.repository import Gtk

from opendrop.gtk_specific.GtkView import GtkView
from opendrop.mvp.View import View


class GtkWindowView(GtkView):

    """Implementation of View that uses the Python GTK+ 3 library, managed by `GtkApplication`. Each view represents a
    window.

    Attributes:
        TITLE   The title of the window, if None, then defaults to class name of view.
        gtk_app The Gtk.Application object.
        window  The view's Gtk.ApplicationWindow object, widgets should be added to this.
    """

    TITLE = None  # type: str

    def __init__(self, gtk_app: Gtk.Application, transient_for: Optional['GtkWindowView'] = None,
                 modal: bool = False) -> None:
        super().__init__(gtk_app)

        self._initialized = False  # type: bool

        self.window = Gtk.ApplicationWindow(application=gtk_app)  # type: Gtk.ApplicationWindow
        self.window.props.title = self.TITLE or type(self).__name__

        self.window.props.transient_for = transient_for.window if transient_for else None
        self.window.props.modal = modal

        self.window.connect('delete-event', self.handle_window_delete_event)

        self.events.on_setup_done.connect(self.post_setup, once=True)

    def post_setup(self) -> None:
        if not self.hidden:
            self.window.present()

        self._initialized = True

    @View.hidden.setter
    def hidden(self, value: bool) -> None:
        View.hidden.__set__(self, value)

        if not self._initialized or self.destroyed:
            return

        if value:
            self.window.hide()
        else:
            self.window.show()

    def destroy(self) -> None:
        View.destroy(self)

        self.window.destroy()

    def handle_window_delete_event(self, *args) -> bool:
        self.events.on_request_close.fire()

        # Return true to block the window from closing
        return True
