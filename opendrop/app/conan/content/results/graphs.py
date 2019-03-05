import itertools
import math
from typing import Sequence, Tuple, Optional

from gi.repository import Gtk
from matplotlib import ticker
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas
from matplotlib.figure import Figure

from opendrop.app.conan.model.results_explorer import ConanResultsExplorer
from opendrop.component.gtk_widget_view import GtkWidgetView
from opendrop.utility.simplebindable import AccessorBindable


class GraphsView(GtkWidgetView[Gtk.Stack]):
    def __init__(self) -> None:
        self.widget = Gtk.Stack(margin=5)

        self._insufficient_data_lbl = Gtk.Label()
        self._insufficient_data_lbl.set_markup('<b>Waiting for data...</b>')
        self.widget.add(self._insufficient_data_lbl)

        graphs_fig = Figure(tight_layout=True)

        self._graphs_fig_canvas = FigureCanvas(graphs_fig)
        self._graphs_fig_canvas.props.hexpand = True
        self._graphs_fig_canvas.props.vexpand = True
        self.widget.add(self._graphs_fig_canvas)

        self._left_angle_axes = graphs_fig.add_subplot(2, 1, 1)
        self._left_angle_axes.set_ylabel('Left angle (degrees)')
        right_angle_axes = graphs_fig.add_subplot(2, 1, 2, sharex=self._left_angle_axes)
        right_angle_axes.xaxis.set_ticks_position('both')
        right_angle_axes.set_ylabel('Right angle (degrees)')

        # Format the labels to show degrees instead of radians.
        self._left_angle_axes.get_yaxis().set_major_formatter(ticker.FuncFormatter(
            lambda x, pos: '{:.4g}'.format(math.degrees(x))))
        right_angle_axes.get_yaxis().set_major_formatter(ticker.FuncFormatter(
            lambda x, pos: '{:.4g}'.format(math.degrees(x))))

        for lbl in self._left_angle_axes.get_xticklabels():
            lbl.set_visible(False)

        self._left_angle_line = self._left_angle_axes.plot([], marker='o', color='blue')[0]
        self._right_angle_line = right_angle_axes.plot([], marker='o', color='blue')[0]

        self.widget.show_all()

        # Wiring things up
        self.bn_left_angle_data = AccessorBindable(setter=self._set_left_angle_data)
        self.bn_right_angle_data = AccessorBindable(setter=self._set_right_angle_data)

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
        else:
            self.widget.set_visible_child(self._insufficient_data_lbl)

        self._sufficient_data = value

    def _update_xlim(self) -> None:
        all_xdata = [*itertools.chain(self._left_angle_line.get_xdata(), self._right_angle_line.get_xdata())]
        if len(all_xdata) <= 1:
            return

        self._left_angle_axes.set_xlim(min(all_xdata), max(all_xdata))

    def _set_left_angle_data(self, data: Sequence[Tuple[float, float]]) -> None:
        if len(data) <= 1:
            return

        self._left_angle_line.set_data(*zip(*data))
        self._update_xlim()
        self._left_angle_axes.relim()
        self._left_angle_axes.margins(y=0.1)

        self._graphs_fig_canvas.queue_draw()

    def _set_right_angle_data(self, data: Sequence[Tuple[float, float]]) -> None:
        if len(data) <= 1:
            return

        self._right_angle_line.set_data(*zip(*data))
        self._update_xlim()
        self._right_angle_line.axes.relim()
        self._right_angle_line.axes.margins(y=0.1)

        self._graphs_fig_canvas.queue_draw()


class GraphsPresenter:
    def __init__(self, summary_data: Optional[ConanResultsExplorer.SummaryData], view: GraphsView) -> None:
        self._summary_data = summary_data
        self._view = view

        self.__destroyed = False
        self.__cleanup_tasks = []

        self._check_if_enough_data_for_graphs()

        if self._summary_data is None:
            return

        data_bindings = [
            self._summary_data.bn_left_angle_data.bind_to(self._view.bn_left_angle_data),
            self._summary_data.bn_right_angle_data.bind_to(self._view.bn_right_angle_data)]
        self.__cleanup_tasks.extend(db.unbind for db in data_bindings)

        event_connections = [
            self._summary_data.bn_left_angle_data.on_changed.connect(self._check_if_enough_data_for_graphs),
            self._summary_data.bn_right_angle_data.on_changed.connect(self._check_if_enough_data_for_graphs)]
        self.__cleanup_tasks.extend(ec.disconnect for ec in event_connections)

    def _check_if_enough_data_for_graphs(self) -> None:
        summary_data = self._summary_data
        if summary_data is None:
            self._view.sufficient_data = False
            return

        ift_data = summary_data.bn_left_angle_data.get()
        volume_data = summary_data.bn_right_angle_data.get()

        min_num_points = min(len(ift_data), len(volume_data))
        if min_num_points <= 1:
            self._view.sufficient_data = False
        else:
            self._view.sufficient_data = True

    def destroy(self) -> None:
        assert not self.__destroyed
        for f in self.__cleanup_tasks:
            f()
        self.__destroyed = True
