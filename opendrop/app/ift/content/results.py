from typing import Optional

from gi.repository import Gtk

from opendrop.app.ift.analysis_model.results_explorer import IFTResultsExplorer
from opendrop.component.gtk_widget_view import GtkWidgetView
from opendrop.iftcalc.analyser import IFTDropAnalysis


class IFTResultsView(GtkWidgetView[Gtk.Grid]):
    def __init__(self) -> None:
        self.widget = Gtk.Grid()
        self.widget.add(Gtk.Label('Results root view'))
        self.widget.show_all()


class _IFTResultsPresenter:
    def __init__(self, results_explorer: IFTResultsExplorer, view: IFTResultsView) -> None:
        self._results_explorer = results_explorer
        self._view = view
        self.__cleanup_tasks = []

        event_connections = [
            self._results_explorer.individual_drops.on_delitem.connect(
                self._hdl_results_explorer_individual_drops_delitem, immediate=True),
            self._results_explorer.individual_drops.on_insert.connect(
                self._hdl_results_explorer_individual_drops_insert, immediate=True),
        ]

        for i, drop in enumerate(self._results_explorer.individual_drops):
            self._hdl_results_explorer_individual_drops_insert(i, drop)

        self.__cleanup_tasks = [ec.disconnect for ec in event_connections]

    def _hdl_results_explorer_individual_drops_delitem(self, i: int) -> None:
        pass

    def _hdl_results_explorer_individual_drops_insert(self, i: int, drop: IFTDropAnalysis) -> None:
        pass

    def destroy(self) -> None:
        for f in self.__cleanup_tasks:
            f()
        self.__cleanup_tasks = []


class IFTResultsPresenter:
    def __init__(self, results_explorer: IFTResultsExplorer, view: IFTResultsView) -> None:
        self._results_explorer = results_explorer
        self._root_view = view
        self._root_presenter = None  # type: Optional[IFTResultsPresenter]

    def enter(self) -> None:
        self._root_presenter = _IFTResultsPresenter(
            results_explorer=self._results_explorer,
            view=self._root_view)

    def leave(self) -> None:
        self._root_presenter.destroy()

    def destroy(self) -> None:
        pass
