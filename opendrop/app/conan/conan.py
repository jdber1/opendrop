from gi.repository import Gtk

from opendrop.gtk_specific.gtk_widget_view import GtkWidgetView
from opendrop.gtk_specific.stack import StackModel
from opendrop.utility.speaker import Speaker, Moderator


class ConanRootView(GtkWidgetView[Gtk.Grid]):
    def __init__(self) -> None:
        self.widget = Gtk.Grid()

        ift_lbl = Gtk.Label(label='Contact angle root view.')
        self.widget.attach(ift_lbl, 0, 0, 1, 1)

        self.widget.show_all()


class ConanRootPresenter:
    def __init__(self, main_mod: Moderator, view: ConanRootView):
        pass


class ConanSpeaker(Speaker):
    def __init__(self, content_model: StackModel) -> None:
        super().__init__()

        self.content_model = content_model

        root_view = ConanRootView()
        self.root_view_key = object()

        content_model.add_child(self.root_view_key, root_view)

    def do_activate(self):
        self.content_model.visible_child_key = self.root_view_key
