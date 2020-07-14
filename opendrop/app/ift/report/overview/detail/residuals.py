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

from gi.repository import GObject
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas

from opendrop.app.ift.analysis import IFTDropAnalysis
from opendrop.appfw import componentclass


@componentclass()
class IFTReportOverviewResiduals(FigureCanvas):
    __gtype_name__ = 'IFTReportOverviewResiduals'

    _analysis = None
    _event_connections = ()

    def __init__(self) -> None:
        from matplotlib.figure import Figure

        figure = Figure(tight_layout=True)
        super().__init__(figure)

        self._axes = figure.add_subplot(1, 1, 1)

        # Set tick labels font size
        for item in (*self._axes.get_xticklabels(), *self._axes.get_yticklabels()):
            item.set_fontsize(8)

    def do_map(self) -> None:
        FigureCanvas.do_map.invoke(FigureCanvas, self)
        self.draw()

    @GObject.Property
    def analysis(self) -> Optional[IFTDropAnalysis]:
        return self._analysis

    @analysis.setter
    def analysis(self, value: Optional[IFTDropAnalysis]) -> None:
        for conn in self._event_connections:
            conn.disconnect()
        self._event_connections = ()
        
        self._analysis = value

        if self._analysis is None:
            return

        self._event_connections = (
            self._analysis.bn_residuals.on_changed.connect(self._hdl_analysis_residuals_changed),
        )

        self._hdl_analysis_residuals_changed()

    def _hdl_analysis_residuals_changed(self) -> None:
        if self._analysis is None: return

        residuals = self._analysis.bn_residuals.get()

        axes = self._axes
        axes.clear()

        if residuals is None or len(residuals) == 0:
            axes.set_axis_off()
            self.draw()
            return

        axes.set_axis_on()
        axes.plot(residuals[:, 0], residuals[:, 1], color='#0080ff', marker='o', linestyle='')
        self.draw()

    def do_destroy(self) -> None:
        for conn in self._event_connections:
            conn.disconnect()
        FigureCanvas.do_destroy.invoke(FigureCanvas, self)
