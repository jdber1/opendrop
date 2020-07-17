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


from typing import Optional, Sequence
from injector import inject

from gi.repository import GObject, Gtk

from opendrop.app.ift.analysis import IFTDropAnalysis
from opendrop.app.ift.services.report import IFTReportService
from opendrop.appfw import Presenter, component


@component(
    template_path='./overview.ui',
)
class IFTReportOverviewPresenter(Presenter[Gtk.Paned]):
    _selection = None
    _event_connections = ()

    @inject
    def __init__(self, report_service: IFTReportService) -> None:
        self.report_service = report_service

        self._event_connections = [
            self.report_service.bn_analyses.on_changed.connect(lambda: self.notify('analyses'), weak_ref=False)
        ]

    @GObject.Property
    def selection(self) -> Optional[IFTDropAnalysis]:
        return self._selection

    @selection.setter
    def selection(self, value: Optional[IFTDropAnalysis]) -> None:
        self._selection = value

    @GObject.Property
    def analyses(self) -> Sequence[IFTDropAnalysis]:
        return self.report_service.bn_analyses.get()

    def destroy(self, *_) -> None:
        for conn in self._event_connections:
            conn.disconnect()
