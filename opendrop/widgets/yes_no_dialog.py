from gi.repository import Gtk


class YesNoDialog(Gtk.MessageDialog):
    def __init__(self, **options) -> None:
        super().__init__(
            flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            resizable=False,
            **options
        )
