from typing import Optional

from gi.repository import Gtk

from opendrop.component.gtk_widget_view import GtkWidgetView


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


class IFTResultsPageContent:
    def __init__(self) -> None:
        self._root_view = IFTResultsView()
        self._root_presenter = None  # type: Optional[IFTResultsPresenter]

    @property
    def view(self) -> GtkWidgetView:
        return self._root_view

    def activate(self) -> None:
        self._root_presenter = IFTResultsPresenter(
            view=self._root_view)

    def deactivate(self) -> None:
        assert self._root_presenter is not None
        self._root_presenter.destroy()
