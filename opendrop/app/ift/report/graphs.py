# Copyright © 2020, Joseph Berry, Rico Tabor (opendrop.dev@gmail.com)
# OpenDrop is released under the GNU GPL License. You are free to
# modify and distribute the code, but always under the same license
# (i.e. you cannot make commercial derivatives).
#
# If you use this software in your research, please cite the following
# journal articles:
#
# J. D. Berry, M. J. Neeson, R. R. Dagastine, D. Y. C. Chan and
# R. F. Tabor, Measurement of surface and interfacial tension using
# pendant drop tensiometry. Journal of Colloid and Interface Science 454
# (2015) 226–237. https://doi.org/10.1016/j.jcis.2015.05.012
#
# E. Huang, T. Denning, A. Skoufis, J. Qi, R. R. Dagastine, R. F. Tabor
# and J. D. Berry, OpenDrop: Open-source software for pendant drop
# tensiometry & contact angle measurements, submitted to the Journal of
# Open Source Software
#
# These citations help us not only to understand who is using and
# developing OpenDrop, and for what purpose, but also to justify
# continued development of this code and other open source resources.
#
# OpenDrop is distributed WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.  You
# should have received a copy of the GNU General Public License along
# with this software.  If not, see <https://www.gnu.org/licenses/>.


from typing import Sequence, Tuple

from gi.repository import Gtk
from matplotlib import ticker
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas
from matplotlib.figure import Figure

from opendrop.app.ift.services.report.graphs import IFTReportGraphsService
from opendrop.appfw import Inject, TemplateChild, componentclass


@componentclass(
    template_path='./graphs.ui',
)
class IFTReportGraphs(Gtk.Stack):
    __gtype_name__ = 'IFTReportGraphs'

    _no_data_label = TemplateChild('no_data_label')
    _figure_container = TemplateChild('figure_container')

    _graphs_service = Inject(IFTReportGraphsService)

    def after_template_init(self) -> None:
        figure = Figure(tight_layout=True)

        self._figure_canvas = FigureCanvas(figure)
        self._figure_canvas.props.hexpand = True
        self._figure_canvas.props.vexpand = True
        self._figure_canvas.props.visible = True
        self._figure_container.add(self._figure_canvas)

        self._ift_axes = figure.add_subplot(3, 1, 1)
        self._ift_axes.set_ylabel('IFT (mN/m)')
        volume_axes = figure.add_subplot(3, 1, 2, sharex=self._ift_axes)
        volume_axes.xaxis.set_ticks_position('both')
        volume_axes.set_ylabel('Vol. (mm³)')
        surface_area_axes = figure.add_subplot(3, 1, 3, sharex=self._ift_axes)
        surface_area_axes.xaxis.set_ticks_position('both')
        surface_area_axes.set_ylabel('Sur. (mm²)')

        # Format the labels to scale to the right units.
        self._ift_axes.get_yaxis().set_major_formatter(ticker.FuncFormatter(lambda x, pos: '{:.4g}'.format(x * 1e3)))
        volume_axes.get_yaxis().set_major_formatter(ticker.FuncFormatter(lambda x, pos: '{:.4g}'.format(x * 1e9)))
        surface_area_axes.get_yaxis().set_major_formatter(ticker.FuncFormatter(lambda x, pos: '{:.4g}'.format(x * 1e6)))

        for lbl in (*self._ift_axes.get_xticklabels(), *volume_axes.get_xticklabels()):
            lbl.set_visible(False)

        self._ift_line = self._ift_axes.plot([], marker='o', color='red')[0]
        self._volume_line = volume_axes.plot([], marker='o', color='blue')[0]
        self._surface_area_line = surface_area_axes.plot([], marker='o', color='green')[0]

        self._graphs_service.connect('notify::ift', self._hdl_model_data_changed)
        self._graphs_service.connect('notify::volume', self._hdl_model_data_changed)
        self._graphs_service.connect('notify::surface-area', self._hdl_model_data_changed)

        self._hdl_model_data_changed()

    def _hdl_model_data_changed(self, *args) -> None:
        ift_data = self._graphs_service.ift
        volume_data = self._graphs_service.volume
        surface_area_data = self._graphs_service.surface_area

        if (
                len(ift_data[0]) <= 1 and
                len(volume_data[0]) <= 1 and
                len(surface_area_data[0]) <= 1
        ):
            self._show_waiting_placeholder()
            return

        self._hide_waiting_placeholder()

        self._set_ift_data(ift_data)
        self._set_volume_data(volume_data)
        self._set_surface_area_data(surface_area_data)

    def _show_waiting_placeholder(self) -> None:
        self.set_visible_child(self._no_data_label)

    def _hide_waiting_placeholder(self) -> None:
        self.set_visible_child(self._figure_container)

    def _set_ift_data(self, data: Sequence[Tuple[float, float]]) -> None:
        if len(data[0]) <= 1:
            return

        self._ift_line.set_data(data)

        self._update_xlim()

        self._ift_axes.relim()
        self._ift_axes.margins(y=0.1)

        self._figure_canvas.draw()

    def _set_volume_data(self, data: Sequence[Tuple[float, float]]) -> None:
        if len(data[0]) <= 1:
            return

        self._volume_line.set_data(data)

        self._update_xlim()

        self._volume_line.axes.relim()
        self._volume_line.axes.margins(y=0.1)

        self._figure_canvas.draw()

    def _set_surface_area_data(self, data: Sequence[Tuple[float, float]]) -> None:
        if len(data[0]) <= 1:
            return

        self._surface_area_line.set_data(data)

        self._update_xlim()

        self._surface_area_line.axes.relim()
        self._surface_area_line.axes.margins(y=0.1)

        self._figure_canvas.draw()

    def _update_xlim(self) -> None:
        all_xdata = (
            *self._ift_line.get_xdata(),
            *self._volume_line.get_xdata(),
            *self._surface_area_line.get_xdata(),
        )

        if len(all_xdata) <= 1:
            return

        xmin = min(all_xdata)
        xmax = max(all_xdata)

        if xmin == xmax:
            return

        self._ift_axes.set_xlim(xmin, xmax)
