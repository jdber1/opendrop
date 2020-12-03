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


import math
from typing import Sequence, Iterable

from gi.repository import Gtk, GObject
from injector import inject
from matplotlib import ticker
from matplotlib.backends.backend_gtk3cairo import FigureCanvasGTK3Cairo as FigureCanvas
from matplotlib.figure import Figure

from opendrop.app.conan.analysis import ConanAnalysis
from opendrop.appfw import Presenter, TemplateChild, component, install

from .services.graphs import ConanReportGraphsService


@component(
    template_path='./graphs.ui',
)
class ConanReportGraphsPresenter(Presenter[Gtk.Stack]):
    no_data_label = TemplateChild('no_data_label')
    figure_container = TemplateChild('figure_container')  # type: TemplateChild[Gtk.Container]

    _analyses = ()

    @inject
    def __init__(self, graphs_service: ConanReportGraphsService) -> None:
        self.graphs_service = graphs_service

    def after_view_init(self) -> None:
        figure = Figure(tight_layout=True)

        self.figure_canvas = FigureCanvas(figure)
        self.figure_canvas.props.hexpand = True
        self.figure_canvas.props.vexpand = True
        self.figure_canvas.props.visible = True
        self.figure_container.add(self.figure_canvas)

        self.left_angle_axes = figure.add_subplot(2, 1, 1)
        self.left_angle_axes.set_ylabel('Left (degrees)')
        right_angle_axes = figure.add_subplot(2, 1, 2, sharex=self.left_angle_axes)
        right_angle_axes.xaxis.set_ticks_position('both')
        right_angle_axes.set_ylabel('Right (degrees)')

        # Format the labels to scale to the right units.
        self.left_angle_axes.get_yaxis().set_major_formatter(
            ticker.FuncFormatter(
                lambda x, pos: '{:.4g}'.format(math.degrees(x))
            )
        )
        right_angle_axes.get_yaxis().set_major_formatter(
            ticker.FuncFormatter(
                lambda x, pos: '{:.4g}'.format(math.degrees(x))
            )
        )

        for lbl in self.left_angle_axes.get_xticklabels():
            lbl.set_visible(False)

        self._left_angle_line = self.left_angle_axes.plot([], marker='o', color='blue')[0]
        self._right_angle_line = right_angle_axes.plot([], marker='o', color='blue')[0]
        self.graphs_service.connect('notify::left-angle', self.data_changed)
        self.graphs_service.connect('notify::right-angle', self.data_changed)

    @install
    @GObject.Property
    def analyses(self) -> Sequence[ConanAnalysis]:
        return self._analyses

    @analyses.setter
    def analyses(self, analyses: Iterable[ConanAnalysis]) -> None:
        self._analyses = tuple(analyses)
        self.graphs_service.analyses = analyses

    def data_changed(self, *_) -> None:
        left_angle_data = self.graphs_service.left_angle
        right_angle_data = self.graphs_service.right_angle

        if len(left_angle_data) <= 1 and len(right_angle_data) <=1:
            self.show_waiting_placeholder()

        self.hide_waiting_placeholder()

        self._left_angle_line.set_data(left_angle_data)
        self._right_angle_line.set_data(right_angle_data)

        self.update_xlim()

        self.left_angle_axes.relim()
        self.left_angle_axes.margins(y=0.1)
        self._right_angle_line.axes.relim()
        self._right_angle_line.axes.margins(y=0.1)

        self.figure_canvas.draw()

    def update_xlim(self) -> None:
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

        self.left_angle_axes.set_xlim(xmin, xmax)

    def show_waiting_placeholder(self) -> None:
        self.host.set_visible_child(self.no_data_label)

    def hide_waiting_placeholder(self) -> None:
        self.host.set_visible_child(self.figure_container)
