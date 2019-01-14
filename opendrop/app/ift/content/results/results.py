from typing import Optional

from gi.repository import Gtk, Gdk

from opendrop.app.ift.model.analyser import IFTDropAnalysis
from opendrop.app.ift.model.results_explorer import IFTResultsExplorer
from opendrop.component.gtk_widget_view import GtkWidgetView
from .graphs import GraphsView
from .individual import IndividualFitView


class IFTResultsView(GtkWidgetView[Gtk.Grid]):
    STYLE = '''
    .ift-results-main-stack-switcher > * {
         min-width: 60px;
         min-height: 0px;
         padding: 6px 4px 6px 4px;
    }
    '''

    _STYLE_PROV = Gtk.CssProvider()
    _STYLE_PROV.load_from_data(bytes(STYLE, 'utf-8'))
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), _STYLE_PROV, Gtk.STYLE_PROVIDER_PRIORITY_USER)

    def __init__(self) -> None:
        self.widget = Gtk.Grid(row_spacing=10, column_spacing=10)

        switcher = Gtk.Box()
        switcher.get_style_context().add_class('linked')

        self._frame = Gtk.Frame(margin=10, label_xalign=0.5)
        self.widget.attach(self._frame, 0, 1, 1, 1)

        stack = Gtk.Stack()
        self._frame.add(stack)

        self.individual_fit = IndividualFitView()
        stack.add_titled(self.individual_fit.widget, name='Individual Fit', title='Individual Fit')

        self.graphs = GraphsView()
        stack.add_titled(self.graphs.widget, name='Graphs', title='Graphs')

        stack_switcher = Gtk.StackSwitcher(stack=stack)
        stack_switcher.get_style_context().add_class('ift-results-main-stack-switcher')

        self._frame.props.label_widget = stack_switcher
        stack.props.visible_child = self.individual_fit.widget

        self.widget.show_all()

    def _hide_graphs(self) -> None:
        self._frame.props.shadow_type = Gtk.ShadowType.NONE
        self._frame.props.label_widget.hide()

    def _show_graphs(self) -> None:
        self._frame.props.shadow_type = Gtk.ShadowType.IN
        self._frame.props.label_widget.show()


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
