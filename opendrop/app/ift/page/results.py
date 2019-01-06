from typing import Optional

from gi.repository import Gtk

from opendrop.component.gtk_widget_view import GtkWidgetView
from opendrop.component.stack import StackModel
from opendrop.utility.speaker import Speaker


class IFTResultsView(GtkWidgetView[Gtk.Grid]):
    def __init__(self) -> None:
        self.widget = Gtk.Grid()
        self.widget.add(Gtk.Label('Results root view'))
        self.widget.show_all()


class IFTResultsPresenter:
    def __init__(self, view: IFTResultsView) -> None:
        self._view = view

    def destroy(self) -> None:
        pass


class IFTResultsSpeaker(Speaker):
    def __init__(self, content_stack: StackModel) -> None:
        super().__init__()

        self._content_stack = content_stack

        self._root_view = IFTResultsView()
        self._root_presenter = None  # type: Optional[IFTResultsPresenter]

        self._root_view_stack_key = object()
        self._content_stack.add_child(self._root_view_stack_key, self._root_view)

    def do_activate(self) -> None:
        self._root_presenter = IFTResultsPresenter(
            view=self._root_view
        )

        # Make root view visible.
        self._content_stack.visible_child_key = self._root_view_stack_key

    def do_deactivate(self) -> None:
        assert self._root_presenter is not None
        self._root_presenter.destroy()
