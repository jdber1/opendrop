import functools

from gi.repository import Gtk

from opendrop.mvp.View import View


class GtkApplicationWindowView(View):
    TITLE = None

    def __init__(self, gtk_app) -> None:
        self.gtk_app = gtk_app
        self.window = Gtk.ApplicationWindow(application=gtk_app, title=(self.TITLE or type(self).__name__))

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
