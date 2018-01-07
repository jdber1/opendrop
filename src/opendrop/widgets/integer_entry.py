# TODO: Have a look at Gtk.Entry signals and use a more appropriate signal for checking and sanitising input other than
# the 'changed' event.

from gi.repository import Gtk


class IntegerEntry(Gtk.Entry):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connect('changed', self.handle_changed)

    def handle_changed(self, _):
        text = self.props.text.strip()
        self.props.text = ''.join([i for i in text if i in '0123456789'])
