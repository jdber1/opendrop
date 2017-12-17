from gi.repository import Gtk

from opendrop.mvp.View import View


class GtkView(View):

    """Implementation of View that uses the Python GTK+ 3 library, managed by `GtkApplication`. Each view represents a
    window.

    Attributes:
        TITLE   The title of the window, if None, then defaults to class name of view.
        gtk_app The Gtk.Application object.
        window  The view's Gtk.ApplicationWindow object, widgets should be added to this.
    """

    TITLE = None  # type: str

    def __init__(self, window: Gtk.ApplicationWindow) -> None:
        self.window = window
        self.window.props.title = self.TITLE or type(self).__name__

        View.__init__(self)

        self.window.connect('delete-event', self._on_delete_event)

        self.window.present()

    def _on_delete_event(self, *args) -> bool:
        self.fire('on_request_close')

        return True

    def maximize(self) -> None:
        self.window.maximize()

    def unmaximize(self) -> None:
        self.window.unmaximize()

    def destroy(self) -> None:
        View.destroy(self)

        self.window.destroy()
