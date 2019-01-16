from typing import Optional

from gi.repository import Gtk, Gdk

from opendrop.app.ift.model.results_explorer import IFTResultsExplorer
from opendrop.component.gtk_widget_view import GtkWidgetView
from .graphs import GraphsView, GraphsPresenter
from .individual import IndividualFitView, IndividualFitPresenter


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

        # # DEBUG
        # time_data = np.linspace(0, 100, 10)
        # ift_data = np.random.rand(10)
        # vol_data = np.random.rand(10)
        # sur_data = np.random.rand(10)
        #
        # self.graphs.bn_time_data.set(time_data)
        # self.graphs.bn_ift_data.set(ift_data)
        # self.graphs.bn_volume_data.set(vol_data)
        # self.graphs.bn_surface_area_data.set(sur_data)
        # # END DEBUG

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
        self.__destroyed = False
        self.__cleanup_tasks = []

        self._individual_fit = IndividualFitPresenter(
            drops=self._results_explorer.individual_drops, view=self._view.individual_fit)
        self.__cleanup_tasks.append(self._individual_fit.destroy)

        self._graphs = GraphsPresenter(
            summary_data=self._results_explorer.summary_data, view=self._view.graphs)
        self.__cleanup_tasks.append(self._graphs.destroy)

    def destroy(self) -> None:
        assert not self.__destroyed
        for f in self.__cleanup_tasks:
            f()
        self.__destroyed = True


class IFTResultsPresenter:
    def __init__(self, results_explorer: IFTResultsExplorer, view: IFTResultsView) -> None:
        self._results_explorer = results_explorer
        self._root_view = view
        self._root_presenter = None  # type: Optional[IFTResultsPresenter]

        self.__enabled = False
        self.__destroyed = False

    def enter(self) -> None:
        if self.__enabled or self.__destroyed:
            return

        self._root_presenter = _IFTResultsPresenter(results_explorer=self._results_explorer, view=self._root_view)
        self.__enabled = True

    def leave(self) -> None:
        if not self.__enabled or self.__destroyed:
            return

        self._root_presenter.destroy()
        self.__enabled = False

    def destroy(self) -> None:
        assert not self.__destroyed
        self.leave()
        self.__destroyed = True
