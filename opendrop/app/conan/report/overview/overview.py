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


from typing import Optional, Iterable, Sequence

from gi.repository import GObject

from opendrop.app.conan.services.analysis import ConanAnalysisJob
from opendrop.appfw import Presenter, component, install


@component(
    template_path='./overview.ui',
)
class ConanReportOverviewPresenter(Presenter):
    _analyses = ()
    _selection = None

    @install
    @GObject.Property
    def analyses(self) -> Sequence[ConanAnalysisJob]:
        return self._analyses

    @analyses.setter
    def analyses(self, analyses: Iterable[ConanAnalysisJob]) -> None:
        self._analyses = tuple(analyses)

    @GObject.Property
    def selection(self) -> Optional[ConanAnalysisJob]:
        return self._selection

    @selection.setter
    def selection(self, selection: Optional[ConanAnalysisJob]) -> None:
        self._selection = selection
