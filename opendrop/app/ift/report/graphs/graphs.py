# Copyright © 2020, Joseph Berry, Rico Tabor (opendrop.dev@gmail.com)
# OpenDrop is released under the GNU GPL License. You are free to
# modify and distribute the code, but always under the same license
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


from typing import Iterable, Sequence, Tuple

from gi.repository import Gtk, GObject
from injector import inject
from matplotlib import ticker
from matplotlib.backends.backend_gtk3cairo import FigureCanvasGTK3Cairo as FigureCanvas
from matplotlib.figure import Figure

from opendrop.app.ift.services.analysis import PendantAnalysisJob
from opendrop.appfw import Presenter, TemplateChild, component, install

from .services.graphs import IFTReportGraphsService


@component(
    template_path='./graphs.ui',
)
class IFTReportGraphsPresenter(Presenter[Gtk.Stack]):
    spinner: TemplateChild[Gtk.Spinner] = TemplateChild('spinner')
    figure_container: TemplateChild[Gtk.Container] = TemplateChild('figure_container')

    _analyses = ()

    @inject
    def __init__(self, graphs_service: IFTReportGraphsService) -> None:
        self.graphs_service = graphs_service

    def after_view_init(self) -> None:
        figure = Figure(tight_layout=False)
        self.figure = figure

        self.figure_canvas = FigureCanvas(figure)
        self.figure_canvas.props.hexpand = True
        self.figure_canvas.props.vexpand = True
        self.figure_canvas.props.visible = True
        self.figure_container.add(self.figure_canvas)

        self.figure_canvas_mapped = False

        self.figure_canvas.connect('map', self.hdl_canvas_map)
        self.figure_canvas.connect('unmap', self.hdl_canvas_unmap)
        self.figure_canvas.connect('size-allocate', self.hdl_canvas_size_allocate)

        self.ift_axes, volume_axes, surface_area_axes = figure.subplots(3, 1, sharex='col')
        self.ift_axes.set_ylabel('IFT [mN/m]')
        self.ift_axes.tick_params(axis='x', direction='inout')
        volume_axes.xaxis.set_ticks_position('both')
        volume_axes.tick_params(axis='x', direction='inout')
        volume_axes.set_ylabel('V [mm³]')
        surface_area_axes.xaxis.set_ticks_position('both')
        surface_area_axes.tick_params(axis='x', direction='inout')
        surface_area_axes.set_ylabel('SA [mm²]')

        self.ift_axes.tick_params(axis='y', left=False, labelleft=False, right=True, labelright=True)
        volume_axes.tick_params(axis='y', left=False, labelleft=False, right=True, labelright=True)
        surface_area_axes.tick_params(axis='y', left=False, labelleft=False, right=True, labelright=True)

        self.ift_axes.grid(axis='x', linestyle='--', color="#dddddd")
        volume_axes.grid(axis='x', linestyle='--', color="#dddddd")
        surface_area_axes.grid(axis='x', linestyle='--', color="#dddddd")

        self.ift_axes.grid(axis='y', linestyle='-', color="#dddddd")
        volume_axes.grid(axis='y', linestyle='-', color="#dddddd")
        surface_area_axes.grid(axis='y', linestyle='-', color="#dddddd")

        # Format the labels to scale to the right units.
        self.ift_axes.get_yaxis().set_major_formatter(ticker.FuncFormatter(lambda x, pos: '{:.4g}'.format(x * 1e3)))
        volume_axes.get_yaxis().set_major_formatter(ticker.FuncFormatter(lambda x, pos: '{:.4g}'.format(x * 1e9)))
        surface_area_axes.get_yaxis().set_major_formatter(ticker.FuncFormatter(lambda x, pos: '{:.4g}'.format(x * 1e6)))

        self.ift_line = self.ift_axes.plot([], marker='o', color='red')[0]
        self.volume_line = volume_axes.plot([], marker='o', color='blue')[0]
        self.surface_area_line = surface_area_axes.plot([], marker='o', color='green')[0]

        self.graphs_service.connect('notify::ift', self.hdl_model_data_changed)
        self.graphs_service.connect('notify::volume', self.hdl_model_data_changed)
        self.graphs_service.connect('notify::surface-area', self.hdl_model_data_changed)

        self.hdl_model_data_changed()

    def hdl_canvas_map(self, *_) -> None:
        self.figure_canvas_mapped = True
        self.figure_canvas.draw_idle()

    def hdl_canvas_unmap(self, *_) -> None:
        self.figure_canvas_mapped = False

    def hdl_canvas_size_allocate(self, *_) -> None:
        self.figure.tight_layout(pad=2.0, h_pad=0)
        self.figure.subplots_adjust(hspace=0)

    @install
    @GObject.Property
    def analyses(self) -> Sequence[PendantAnalysisJob]:
        return self._analyses

    @analyses.setter
    def analyses(self, analyses: Iterable[PendantAnalysisJob]) -> None:
        self._analyses = tuple(analyses)
        self.graphs_service.set_analyses(analyses)

    def hdl_model_data_changed(self, *args) -> None:
        ift_data = self.graphs_service.ift
        volume_data = self.graphs_service.volume
        surface_area_data = self.graphs_service.surface_area

        if (
                len(ift_data[0]) <= 1 and
                len(volume_data[0]) <= 1 and
                len(surface_area_data[0]) <= 1
        ):
            self.show_waiting_placeholder()
            return

        self.hide_waiting_placeholder()

        self.set_ift_data(ift_data)
        self.set_volume_data(volume_data)
        self.set_surface_area_data(surface_area_data)

        if self.figure_canvas_mapped:
            self.figure.tight_layout(pad=2.0, h_pad=0)
            self.figure.subplots_adjust(hspace=0)

        self.figure_canvas.draw_idle()

    def show_waiting_placeholder(self) -> None:
        self.host.set_visible_child(self.spinner)
        self.spinner.start()

    def hide_waiting_placeholder(self) -> None:
        self.host.set_visible_child(self.figure_container)
        self.spinner.stop()

    def set_ift_data(self, data: Sequence[Tuple[float, float]]) -> None:
        if len(data[0]) <= 1:
            return

        self.ift_line.set_data(data)

        self.update_xlim()

        self.ift_axes.relim()
        self.ift_axes.margins(y=0.1)

    def set_volume_data(self, data: Sequence[Tuple[float, float]]) -> None:
        if len(data[0]) <= 1:
            return

        self.volume_line.set_data(data)

        self.update_xlim()

        self.volume_line.axes.relim()
        self.volume_line.axes.margins(y=0.1)

    def set_surface_area_data(self, data: Sequence[Tuple[float, float]]) -> None:
        if len(data[0]) <= 1:
            return

        self.surface_area_line.set_data(data)

        self.update_xlim()

        self.surface_area_line.axes.relim()
        self.surface_area_line.axes.margins(y=0.1)

    def update_xlim(self) -> None:
        all_xdata = (
            *self.ift_line.get_xdata(),
            *self.volume_line.get_xdata(),
            *self.surface_area_line.get_xdata(),
        )

        if len(all_xdata) <= 1:
            return

        xmin = min(all_xdata)
        xmax = max(all_xdata)

        if xmin == xmax:
            return

        self.ift_axes.set_xlim(xmin, xmax)
