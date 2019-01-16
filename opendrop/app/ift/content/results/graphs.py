import itertools
from typing import Sequence, Tuple, Optional

from gi.repository import Gtk
from matplotlib import ticker
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas
from matplotlib.figure import Figure

from opendrop.app.ift.model.results_explorer import IFTResultsExplorer
from opendrop.component.gtk_widget_view import GtkWidgetView
from opendrop.utility.bindable.bindable import AtomicBindableAdapter
from opendrop.utility.bindable.binding import Binding


class GraphsView(GtkWidgetView[Gtk.Stack]):
    def __init__(self) -> None:
        self.widget = Gtk.Stack(margin=5)

        self._insufficient_data_lbl = Gtk.Label()
        self._insufficient_data_lbl.set_markup('<b>Waiting for data...</b>')
        self.widget.add(self._insufficient_data_lbl)

        graphs_fig = Figure(tight_layout=True)
        graphs_fig.subplots_adjust(hspace=0)

        self._graphs_fig_canvas = FigureCanvas(graphs_fig)
        self._graphs_fig_canvas.props.hexpand = True
        self._graphs_fig_canvas.props.vexpand = True
        self.widget.add(self._graphs_fig_canvas)

        self._ift_axes = graphs_fig.add_subplot(3, 1, 1)
        self._ift_axes.set_ylabel('IFT (mN/m)')
        volume_axes = graphs_fig.add_subplot(3, 1, 2, sharex=self._ift_axes)
        volume_axes.xaxis.set_ticks_position('both')
        volume_axes.set_ylabel('Vol. (mm³)')
        surface_area_axes = graphs_fig.add_subplot(3, 1, 3, sharex=self._ift_axes)
        surface_area_axes.xaxis.set_ticks_position('both')
        surface_area_axes.set_ylabel('Sur. (mm²)')

        # Format the labels to scale to the right units.
        self._ift_axes.get_yaxis().set_major_formatter(ticker.FuncFormatter(lambda x, pos: '{:.4g}'.format(x*1e3)))
        volume_axes.get_yaxis().set_major_formatter(ticker.FuncFormatter(lambda x, pos: '{:.4g}'.format(x*1e9)))
        surface_area_axes.get_yaxis().set_major_formatter(ticker.FuncFormatter(lambda x, pos: '{:.4g}'.format(x*1e6)))

        for lbl in itertools.chain(self._ift_axes.get_xticklabels(), volume_axes.get_xticklabels()):
            lbl.set_visible(False)

        self._ift_line = self._ift_axes.plot([], marker='o', color='red')[0]
        self._volume_line = volume_axes.plot([], marker='o', color='blue')[0]
        self._surface_area_line = surface_area_axes.plot([], marker='o', color='green')[0]

        self.widget.show_all()

        # Wiring things up
        self.bn_ift_data = AtomicBindableAdapter(setter=self._set_ift_data)
        self.bn_volume_data = AtomicBindableAdapter(setter=self._set_volume_data)
        self.bn_surface_area_data = AtomicBindableAdapter(setter=self._set_surface_area_data)

        # Set initial sufficient_data state.
        self._sufficient_data = False
        self.widget.set_visible_child(self._insufficient_data_lbl)

    @property
    def sufficient_data(self) -> bool:
        return self._sufficient_data

    @sufficient_data.setter
    def sufficient_data(self, value: bool) -> None:
        if self.sufficient_data is value:
            return

        if value:
            self.widget.set_visible_child(self._graphs_fig_canvas)
            self._sufficient_data = value
        else:
            self.widget.set_visible_child(self._insufficient_data_lbl)
            self._sufficient_data = value

    def _update_xlim(self) -> None:
        all_xdata = [*itertools.chain(self._ift_line.get_xdata(), self._volume_line.get_xdata(),
                                      self._surface_area_line.get_xdata())]
        if len(all_xdata) <= 1:
            return

        self._ift_axes.set_xlim(min(all_xdata), max(all_xdata))

    def _set_ift_data(self, data: Sequence[Tuple[float, float]]) -> None:
        if len(data) <= 1:
            return

        self._ift_line.set_data(*zip(*data))
        self._update_xlim()
        self._ift_axes.relim()
        self._ift_axes.margins(y=0.1)

        self._graphs_fig_canvas.queue_draw()

    def _set_volume_data(self, data: Sequence[Tuple[float, float]]) -> None:
        if len(data) <= 1:
            return

        self._volume_line.set_data(*zip(*data))
        self._update_xlim()
        self._volume_line.axes.relim()
        self._volume_line.axes.margins(y=0.1)

        self._graphs_fig_canvas.queue_draw()

    def _set_surface_area_data(self, data: Sequence[Tuple[float, float]]) -> None:
        if len(data) <= 1:
            return

        self._surface_area_line.set_data(*zip(*data))
        self._update_xlim()
        self._surface_area_line.axes.relim()
        self._surface_area_line.axes.margins(y=0.1)

        self._graphs_fig_canvas.queue_draw()


class GraphsPresenter:
    def __init__(self, summary_data: Optional[IFTResultsExplorer.SummaryData], view: GraphsView) -> None:
        self._summary_data = summary_data
        self._view = view

        self.__destroyed = False
        self.__cleanup_tasks = []

        self._check_if_enough_data_for_graphs()

        if self._summary_data is None:
            return

        data_bindings = [
            Binding(self._summary_data.bn_ift_data, self._view.bn_ift_data),
            Binding(self._summary_data.bn_volume_data, self._view.bn_volume_data),
            Binding(self._summary_data.bn_surface_area_data, self._view.bn_surface_area_data)]
        self.__cleanup_tasks.extend(db.unbind for db in data_bindings)

        event_connections = [
            self._summary_data.bn_ift_data.on_changed.connect(self._check_if_enough_data_for_graphs, immediate=True),
            self._summary_data.bn_volume_data.on_changed.connect(self._check_if_enough_data_for_graphs, immediate=True),
            self._summary_data.bn_surface_area_data.on_changed.connect(self._check_if_enough_data_for_graphs,
                                                                       immediate=True)]
        self.__cleanup_tasks.extend(ec.disconnect for ec in event_connections)

    def _check_if_enough_data_for_graphs(self) -> None:
        summary_data = self._summary_data
        if summary_data is None:
            self._view.sufficient_data = False
            return

        ift_data = summary_data.ift_data
        volume_data = summary_data.volume_data
        surface_area_data = summary_data.surface_area_data
        min_num_points = min(len(ift_data), len(volume_data), len(surface_area_data))
        if min_num_points <= 1:
            self._view.sufficient_data = False
        else:
            self._view.sufficient_data = True

    def destroy(self) -> None:
        assert not self.__destroyed
        for f in self.__cleanup_tasks:
            f()
        self.__destroyed = True
