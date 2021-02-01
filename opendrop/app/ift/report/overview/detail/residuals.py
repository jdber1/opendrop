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


from typing import Optional

from gi.repository import GObject, Gtk

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
        self.canvas.show()
        self.host.add(self.canvas)

        self.canvas.connect('map', self.hdl_canvas_map)

        self.axes = figure.add_subplot(1, 1, 1)

        # Set tick labels font size
        for item in (*self.axes.get_xticklabels(), *self.axes.get_yticklabels()):
            item.set_fontsize(8)

    def hdl_canvas_map(self, *_) -> None:
        self.canvas.draw_idle()

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
            self._analysis.bn_arclengths.on_changed.connect(self._hdl_analysis_residuals_changed),
            self._analysis.bn_residuals.on_changed.connect(self._hdl_analysis_residuals_changed),
        )

        self._hdl_analysis_residuals_changed()

    def _hdl_analysis_residuals_changed(self) -> None:
        if self._analysis is None: return

        arclengths = self._analysis.bn_arclengths.get()
        residuals = self._analysis.bn_residuals.get()

        axes = self.axes
        axes.clear()

        if arclengths is None or len(arclengths) == 0:
            axes.set_axis_off()
            self.canvas.draw_idle()
            return

        if residuals is None or len(residuals) == 0:
            axes.set_axis_off()
            self.canvas.draw_idle()
            return

        axes.set_axis_on()
        axes.scatter(arclengths, residuals, color='#0080ff')
        self.canvas.draw_idle()

    def destroy(self, *_) -> None:
        for conn in self.event_connections:
            conn.disconnect()
