from typing import Optional

import numpy as np
from gi.repository import Gtk
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas
from matplotlib.figure import Figure

from opendrop.component.gtk_widget_view import GtkWidgetView
from opendrop.utility.bindable.bindable import AtomicBindableAdapter


class GraphsView(GtkWidgetView[Gtk.Grid]):
    def __init__(self) -> None:
        self.widget = Gtk.Grid(margin=5)

        self._graphs_figure = Figure(tight_layout=True)
        self._graphs_figure.subplots_adjust(hspace=0)

        graphs_figure_canvas = FigureCanvas(self._graphs_figure)
        graphs_figure_canvas.props.hexpand = True
        graphs_figure_canvas.props.vexpand = True
        self.widget.add(graphs_figure_canvas)

        self.widget.show_all()

        self._time_data = None  # type: Optional[np.ndarray]
        self._ift_data = None  # type: Optional[np.ndarray]
        self._volume_data = None  # type: Optional[np.ndarray]
        self._surface_area_data = None  # type: Optional[np.ndarray]

        self.bn_time_data = AtomicBindableAdapter(setter=self._set_time_data)
        self.bn_ift_data = AtomicBindableAdapter(setter=self._set_ift_data)
        self.bn_volume_data = AtomicBindableAdapter(setter=self._set_volume_data)
        self.bn_surface_area_data = AtomicBindableAdapter(setter=self._set_surface_area_data)

    def _set_time_data(self, data: Optional[np.ndarray]) -> None:
        self._time_data = data
        self._draw_graphs()

    def _set_ift_data(self, data: Optional[np.ndarray]) -> None:
        self._ift_data = data
        self._draw_graphs()

    def _set_volume_data(self, data: Optional[np.ndarray]) -> None:
        self._volume_data = data
        self._draw_graphs()

    def _set_surface_area_data(self, data: Optional[np.ndarray]) -> None:
        self._surface_area_data = data
        self._draw_graphs()

    def _draw_graphs(self) -> None:
        self._graphs_figure.clear()

        time_data = self._time_data
        ift_data = self._ift_data
        volume_data = self._volume_data
        surface_area_data = self._surface_area_data
        if any([v is None for v in (time_data, ift_data, volume_data, surface_area_data)]):
            self._graphs_figure.canvas.draw()
            return None

        ift_axes = self._graphs_figure.add_subplot(3, 1, 1)
        ift_axes.set_ylabel('IFT (mN/m)')
        volume_axes = self._graphs_figure.add_subplot(3, 1, 2, sharex=ift_axes)
        volume_axes.xaxis.set_ticks_position('both')
        volume_axes.set_ylabel('Vol. (mm³)')
        surface_area_axes = self._graphs_figure.add_subplot(3, 1, 3, sharex=ift_axes)
        surface_area_axes.xaxis.set_ticks_position('both')
        surface_area_axes.set_ylabel('Sur. (mm²)')

        for lbl in (ift_axes.get_xticklabels() + volume_axes.get_xticklabels()):
            lbl.set_visible(False)

        ift_axes.plot(time_data, ift_data, marker='o', color='red')
        volume_axes.plot(time_data, volume_data, marker='o', color='blue')
        surface_area_axes.plot(time_data, surface_area_data, marker='o', color='green')

        # Set the x limits to be the minimum and maximum times of all data points.
        ift_axes.set_xlim(min(time_data), max(time_data))

        self._graphs_figure.canvas.draw()
