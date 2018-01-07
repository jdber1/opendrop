from gi.repository import Gtk

from opendrop.gtk_specific.GtkView import GtkView
from opendrop.mvp.View import View


class GtkWidgetView(GtkView):

    """Implementation of View that uses the Python GTK+ 3 library, managed by `GtkApplication`. Each view represents a
    window.

    Attributes:
        TITLE   The title of the window, if None, then defaults to class name of view.
        gtk_app The Gtk.Application object.
        window  The view's Gtk.ApplicationWindow object, widgets should be added to this.
    """

    TITLE = None  # type: str

    def __init__(self, gtk_app: Gtk.Application) -> None:
        super().__init__(gtk_app)

        self._initialized = False  # type: bool

        self.container = Gtk.Box()  # type: Gtk.Box

        self.connect('on_setup_done', self.post_setup, once=True)

    def post_setup(self) -> None:
        if not self.hidden:
            self.container.show()

        self._initialized = True

    @View.hidden.setter
    def hidden(self, value: bool) -> None:
        View.hidden.__set__(self, value)

        if not self._initialized or self.destroyed:
            return

        if value:
            self.container.hide()
        else:
            self.container.show()

    def destroy(self) -> None:
        View.destroy(self)

        self.container.destroy()
