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


from typing import Iterable, Sequence, Tuple

from gi.repository import Gtk, GObject
from injector import inject
from matplotlib import ticker
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas
from matplotlib.figure import Figure

from opendrop.app.ift.analysis import IFTDropAnalysis
from opendrop.appfw import Presenter, TemplateChild, component, install

from .services.graphs import IFTReportGraphsService


@component(
    template_path='./graphs.ui',
)
class IFTReportGraphsPresenter(Presenter[Gtk.Stack]):
    no_data_label = TemplateChild('no_data_label')
    figure_container = TemplateChild('figure_container')  # type: TemplateChild[Gtk.Container]

    _analyses = ()

    @inject
    def __init__(self, graphs_service: IFTReportGraphsService) -> None:
        self.graphs_service = graphs_service

    def after_view_init(self) -> None:
        figure = Figure(tight_layout=True)

        self.figure_canvas = FigureCanvas(figure)
        self.figure_canvas.props.hexpand = True
        self.figure_canvas.props.vexpand = True
        self.figure_canvas.props.visible = True
        self.figure_container.add(self.figure_canvas)

        self.ift_axes = figure.add_subplot(3, 1, 1)
        self.ift_axes.set_ylabel('IFT (mN/m)')
        volume_axes = figure.add_subplot(3, 1, 2, sharex=self.ift_axes)
        volume_axes.xaxis.set_ticks_position('both')
        volume_axes.set_ylabel('Vol. (mm³)')
        surface_area_axes = figure.add_subplot(3, 1, 3, sharex=self.ift_axes)
        surface_area_axes.xaxis.set_ticks_position('both')
        surface_area_axes.set_ylabel('Sur. (mm²)')

        # Format the labels to scale to the right units.
        self.ift_axes.get_yaxis().set_major_formatter(ticker.FuncFormatter(lambda x, pos: '{:.4g}'.format(x * 1e3)))
        volume_axes.get_yaxis().set_major_formatter(ticker.FuncFormatter(lambda x, pos: '{:.4g}'.format(x * 1e9)))
        surface_area_axes.get_yaxis().set_major_formatter(ticker.FuncFormatter(lambda x, pos: '{:.4g}'.format(x * 1e6)))

        for lbl in (*self.ift_axes.get_xticklabels(), *volume_axes.get_xticklabels()):
            lbl.set_visible(False)

        self.ift_line = self.ift_axes.plot([], marker='o', color='red')[0]
        self.volume_line = volume_axes.plot([], marker='o', color='blue')[0]
        self.surface_area_line = surface_area_axes.plot([], marker='o', color='green')[0]

        self.graphs_service.connect('notify::ift', self.hdl_model_data_changed)
        self.graphs_service.connect('notify::volume', self.hdl_model_data_changed)
        self.graphs_service.connect('notify::surface-area', self.hdl_model_data_changed)

        self.hdl_model_data_changed()

    @install
    @GObject.Property
    def analyses(self) -> Sequence[IFTDropAnalysis]:
        return self._analyses

    @analyses.setter
    def analyses(self, analyses: Iterable[IFTDropAnalysis]) -> None:
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

    def show_waiting_placeholder(self) -> None:
        self.host.set_visible_child(self.no_data_label)

    def hide_waiting_placeholder(self) -> None:
        self.host.set_visible_child(self.figure_container)

    def set_ift_data(self, data: Sequence[Tuple[float, float]]) -> None:
        if len(data[0]) <= 1:
            return

        self.ift_line.set_data(data)

        self.update_xlim()

        self.ift_axes.relim()
        self.ift_axes.margins(y=0.1)

        self.figure_canvas.draw()

    def set_volume_data(self, data: Sequence[Tuple[float, float]]) -> None:
        if len(data[0]) <= 1:
            return

        self.volume_line.set_data(data)

        self.update_xlim()

        self.volume_line.axes.relim()
        self.volume_line.axes.margins(y=0.1)

        self.figure_canvas.draw()

    def set_surface_area_data(self, data: Sequence[Tuple[float, float]]) -> None:
        if len(data[0]) <= 1:
            return

        self.surface_area_line.set_data(data)

        self.update_xlim()

        self.surface_area_line.axes.relim()
        self.surface_area_line.axes.margins(y=0.1)

        self.figure_canvas.draw()

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
