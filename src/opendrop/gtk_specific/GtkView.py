from gi.repository import Gtk

from opendrop.mvp.View import View


class GtkView(View):
    def __init__(self, gtk_app: Gtk.Application):
        super().__init__()
