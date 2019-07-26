import math
from typing import Sequence, Tuple

from gi.repository import Gtk
from matplotlib import ticker
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas
from matplotlib.figure import Figure

from opendrop.mvp import ComponentSymbol, View, Presenter
from .model import GraphsModel

graphs_cs = ComponentSymbol()  # type: ComponentSymbol[Gtk.Widget]


@graphs_cs.view()
class GraphsView(View['GraphsPresenter', Gtk.Widget]):
    def _do_init(self) -> Gtk.Widget:
        self._widget = Gtk.Stack(margin=5)

        self._waiting_placeholder = Gtk.Label()
        self._waiting_placeholder.set_markup('<b>No data</b>')
        self._widget.add(self._waiting_placeholder)

        figure = Figure(tight_layout=True)

        self._figure_canvas = FigureCanvas(figure)
        self._figure_canvas.props.hexpand = True
        self._figure_canvas.props.vexpand = True
        self._widget.add(self._figure_canvas)

        self._left_angle_axes = figure.add_subplot(2, 1, 1)
        self._left_angle_axes.set_ylabel('Left angle (degrees)')
        right_angle_axes = figure.add_subplot(2, 1, 2, sharex=self._left_angle_axes)
        right_angle_axes.xaxis.set_ticks_position('both')
        right_angle_axes.set_ylabel('Right angle (degrees)')

        # Format the labels to scale to the right units.
        self._left_angle_axes.get_yaxis() \
                             .set_major_formatter(
            ticker.FuncFormatter(
                lambda x, pos: '{:.4g}'.format(math.degrees(x))
            )
        )
        right_angle_axes.get_yaxis() \
                        .set_major_formatter(
            ticker.FuncFormatter(
                lambda x, pos: '{:.4g}'.format(math.degrees(x))
            )
        )

        for lbl in (*self._left_angle_axes.get_xticklabels(), *right_angle_axes.get_xticklabels()):
            lbl.set_visible(False)

        self._left_angle_line = self._left_angle_axes.plot([], marker='o', color='blue')[0]
        self._right_angle_line = right_angle_axes.plot([], marker='o', color='blue')[0]

        self._widget.show_all()

        self.presenter.view_ready()

        return self._widget

    def show_waiting_placeholder(self) -> None:
        self._widget.set_visible_child(self._waiting_placeholder)

    def hide_waiting_placeholder(self) -> None:
        self._widget.set_visible_child(self._figure_canvas)

    def set_left_angle_data(self, data: Sequence[Tuple[float, float]]) -> None:
        if len(data[0]) <= 1:
            return

        self._left_angle_line.set_data(data)

        self._update_xlim()

        self._left_angle_axes.relim()
        self._left_angle_axes.margins(y=0.1)

        self._figure_canvas.queue_draw()

    def set_right_angle_data(self, data: Sequence[Tuple[float, float]]) -> None:
        if len(data[0]) <= 1:
            return

        self._right_angle_line.set_data(data)

        self._update_xlim()

        self._right_angle_line.axes.relim()
        self._right_angle_line.axes.margins(y=0.1)

        self._figure_canvas.queue_draw()

    def _update_xlim(self) -> None:
        all_xdata = (
            *self._left_angle_line.get_xdata(),
            *self._right_angle_line.get_xdata(),
        )

        if len(all_xdata) <= 1:
            return

        xmin = min(all_xdata)
        xmax = max(all_xdata)

        if xmin == xmax:
            return

        self._left_angle_axes.set_xlim(xmin, xmax)

    def _do_destroy(self) -> None:
        self._widget.destroy()


@graphs_cs.presenter(options=['model'])
class GraphsPresenter(Presenter['GraphsView']):
    def _do_init(self, model: GraphsModel) -> None:
        self._model = model
        self.__event_connections = []

    def view_ready(self) -> None:
        self.__event_connections.extend([
            self._model.bn_left_angle_data.on_changed.connect(
                self._hdl_model_data_changed
            ),
            self._model.bn_right_angle_data.on_changed.connect(
                self._hdl_model_data_changed
            ),
        ])

        self._hdl_model_data_changed()

    def _hdl_model_data_changed(self) -> None:
        left_angle_data = self._model.bn_left_angle_data.get()
        right_angle_data = self._model.bn_right_angle_data.get()

        if (
                len(left_angle_data[0]) <= 1 and
                len(right_angle_data[0]) <= 1
        ):
            self.view.show_waiting_placeholder()
            return

        self.view.hide_waiting_placeholder()

        self.view.set_left_angle_data(left_angle_data)
        self.view.set_right_angle_data(right_angle_data)

    def _do_destroy(self) -> None:
        for ec in self.__event_connections:
            ec.disconnect()
