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


import math
from typing import Sequence, Iterable

from gi.repository import Gtk, GObject
from injector import inject
from matplotlib.backends.backend_gtk3cairo import FigureCanvasGTK3Cairo as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter

from opendrop.app.conan.services.analysis import ConanAnalysisJob
from opendrop.appfw import Presenter, TemplateChild, component, install

from .services.graphs import ConanReportGraphsService


@component(
    template_path='./graphs.ui',
)
class ConanReportGraphsPresenter(Presenter[Gtk.Stack]):
    spinner: TemplateChild[Gtk.Spinner] = TemplateChild('spinner')
    figure_container = TemplateChild('figure_container')  # type: TemplateChild[Gtk.Container]

    _analyses = ()

    @inject
    def __init__(self, graphs_service: ConanReportGraphsService) -> None:
        self.graphs_service = graphs_service

    def after_view_init(self) -> None:
        self.figure = Figure(tight_layout=False)

        self.figure_canvas = FigureCanvas(self.figure)
        self.figure_canvas.props.hexpand = True
        self.figure_canvas.props.vexpand = True
        self.figure_canvas.props.visible = True
        self.figure_container.add(self.figure_canvas)

        self.figure_canvas_mapped = False

        self.figure_canvas.connect('map', self.canvas_map)
        self.figure_canvas.connect('unmap', self.canvas_unmap)
        self.figure_canvas.connect('size-allocate', self.canvas_size_allocate)

        left_ca_ax, right_ca_ax = self.figure.subplots(2, 1, sharex='col')

        left_ca_ax.set_ylabel('Left CA [°]')
        left_ca_ax.tick_params(axis='x', direction='inout')

        right_ca_ax.xaxis.set_ticks_position('both')
        right_ca_ax.set_ylabel('Right CA [°]')
        right_ca_ax.tick_params(axis='x', direction='inout')

        left_ca_ax.tick_params(axis='y', left=False, labelleft=False, right=True, labelright=True)
        right_ca_ax.tick_params(axis='y', left=False, labelleft=False, right=True, labelright=True)

        # Format the labels to scale to the right units.
        left_ca_ax.get_yaxis().set_major_formatter(
            FuncFormatter(lambda x, _: '{:.4g}'.format(math.degrees(x)))
        )
        right_ca_ax.get_yaxis().set_major_formatter(
            FuncFormatter(lambda x, _: '{:.4g}'.format(math.degrees(x)))
        )

        left_ca_ax.grid(axis='x', linestyle='--', color="#dddddd")
        left_ca_ax.grid(axis='y', linestyle='-', color="#dddddd")

        right_ca_ax.grid(axis='x', linestyle='--', color="#dddddd")
        right_ca_ax.grid(axis='y', linestyle='-', color="#dddddd")

        self._left_ca_ax = left_ca_ax
        self._left_ca_line = left_ca_ax.plot([], marker='o', color='#0080ff')[0]
        self._right_ca_line = right_ca_ax.plot([], marker='o', color='#ff8000')[0]

        self.graphs_service.connect('notify::left-angle', self.data_changed)
        self.graphs_service.connect('notify::right-angle', self.data_changed)

        self.data_changed()

    def canvas_map(self, *_) -> None:
        self.figure_canvas_mapped = True
        self.figure_canvas.draw_idle()

    def canvas_unmap(self, *_) -> None:
        self.figure_canvas_mapped = False

    def canvas_size_allocate(self, *_) -> None:
        self.figure.tight_layout(pad=2.0, h_pad=0)
        self.figure.subplots_adjust(hspace=0)

    @install
    @GObject.Property
    def analyses(self) -> Sequence[ConanAnalysisJob]:
        return self._analyses

    @analyses.setter
    def analyses(self, analyses: Iterable[ConanAnalysisJob]) -> None:
        self._analyses = tuple(analyses)
        self.graphs_service.analyses = analyses

    def data_changed(self, *_) -> None:
        left_angle_data = self.graphs_service.left_angle
        right_angle_data = self.graphs_service.right_angle

        if left_angle_data.shape[1] <= 1 or right_angle_data.shape[1] <=1:
            self.show_waiting_placeholder()
            return

        self.hide_waiting_placeholder()

        self._left_ca_line.set_data(left_angle_data)
        self._right_ca_line.set_data(right_angle_data)

        self.update_xlim()

        self._left_ca_line.axes.relim()
        self._left_ca_line.axes.margins(y=0.1)
        self._right_ca_line.axes.relim()
        self._right_ca_line.axes.margins(y=0.1)

        self.figure_canvas.draw()

    def update_xlim(self) -> None:
        all_xdata = (
            *self._left_ca_line.get_xdata(),
            *self._right_ca_line.get_xdata(),
        )

        if len(all_xdata) <= 1:
            return

        xmin = min(all_xdata)
        xmax = max(all_xdata)

        if xmin == xmax:
            return

        self._left_ca_ax.set_xlim(xmin, xmax)

    def show_waiting_placeholder(self) -> None:
        self.host.set_visible_child(self.spinner)
        self.spinner.start()

    def hide_waiting_placeholder(self) -> None:
        self.host.set_visible_child(self.figure_container)
        self.spinner.stop()
