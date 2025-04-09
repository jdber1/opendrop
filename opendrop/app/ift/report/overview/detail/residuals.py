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


from typing import Optional

from gi.repository import GObject, Gtk, GLib

from opendrop.app.ift.services.analysis import PendantAnalysisJob
from opendrop.appfw import Presenter, component, install


@component(
    template_path='./residuals.ui',
)
class IFTReportOverviewResidualsPresenter(Presenter[Gtk.Bin]):
    _analysis = None
    event_connections = ()

    def after_view_init(self) -> None:
        from matplotlib.backends.backend_gtk3cairo import FigureCanvasGTK3Cairo
        from matplotlib.figure import Figure

        figure = Figure(tight_layout=True)
        self.canvas = FigureCanvasGTK3Cairo(figure)

        self.canvas_mapped = False
        self.figure_stale = True
        self.queue_draw_canvas_source_id = None
        self.canvas.connect('map', self.canvas_map)
        self.canvas.connect('unmap', self.canvas_unmap)

        self.axes = figure.add_subplot(1, 1, 1)

        # Set tick labels font size
        for item in (*self.axes.get_xticklabels(), *self.axes.get_yticklabels()):
            item.set_fontsize(8)

        self.canvas.show()
        self.host.add(self.canvas)

    def canvas_map(self, *_) -> None:
        self.canvas_mapped = True
        self.update_canvas()
        if self.figure_stale:
            self.canvas.hide()

    def canvas_unmap(self, *_) -> None:
        self.canvas_mapped = False

    def update_canvas(self) -> None:
        if not self.canvas_mapped:
            return

        if not self.figure_stale:
            return

        if self.queue_draw_canvas_source_id is not None:
            return

        self.queue_draw_canvas_source_id = GLib.idle_add(
            priority=GLib.PRIORITY_LOW,
            function=self.draw_canvas,
        )

    def draw_canvas(self) -> None:
        self.queue_draw_canvas_source_id = None

        analysis = self._analysis

        ax = self.axes
        ax.clear()

        if analysis.bn_status.get() is not PendantAnalysisJob.Status.FINISHED:
            ax.set_axis_off()
        else:
            ax.set_axis_on()
            arclengths = analysis.bn_arclengths.get()
            residuals = analysis.bn_residuals.get()
            ax.scatter(arclengths, residuals, color='#0080ff')

        self.figure_stale = False

        self.canvas.draw_idle()
        self.canvas.show()

    @install
    @GObject.Property
    def analysis(self) -> Optional[PendantAnalysisJob]:
        return self._analysis

    @analysis.setter
    def analysis(self, value: Optional[PendantAnalysisJob]) -> None:
        for conn in self.event_connections:
            conn.disconnect()
        self.event_connections = ()

        self._analysis = value

        if self._analysis is None:
            return

        self.event_connections = (
            self._analysis.bn_status.on_changed.connect(self.analysis_status_changed),
        )

        self.analysis_status_changed()

    def analysis_status_changed(self):
        self.figure_stale = True
        self.update_canvas()

    def destroy(self, *_) -> None:
        for conn in self.event_connections:
            conn.disconnect()
