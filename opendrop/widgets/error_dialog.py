from gi.repository import Gtk


class ErrorDialog(Gtk.MessageDialog):
    def __init__(self, **options) -> None:
        super().__init__(
            flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.CLOSE,
            **options
        )
