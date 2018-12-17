from gi.repository import Gtk

from opendrop.component.gtk_widget_view import GtkWidgetView
from opendrop.component.stack import StackModel
from opendrop.utility.speaker import Speaker, Moderator


class IFTRootView(GtkWidgetView[Gtk.Grid]):
    def __init__(self) -> None:
        self.widget = Gtk.Grid()

        ift_lbl = Gtk.Label(label='Interfacial tension root view.')
        self.widget.attach(ift_lbl, 0, 0, 1, 1)

        self.widget.show_all()


class IFTRootPresenter:
    def __init__(self, main_mod: Moderator, view: IFTRootView):
        pass


class IFTSpeaker(Speaker):
    def __init__(self, content_model: StackModel) -> None:
        super().__init__()

        self.content_model = content_model

        root_view = IFTRootView()
        self.root_view_key = object()

        content_model.add_child(self.root_view_key, root_view)

    def do_activate(self):
        self.content_model.visible_child_key = self.root_view_key
