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

from opendrop.appfw import Presenter, component, install

from ._types import AnalysisFooterStatus


@component(
    template_path='./analysis.ui',
)
class AnalysisFooterPresenter(Presenter):
    _status = AnalysisFooterStatus.IN_PROGRESS
    _progress = 0.0

    _time_start = None
    _time_complete = None

    @install
    @GObject.Property
    def status(self) -> AnalysisFooterStatus:
        return self._status

    @status.setter
    def status(self, status: AnalysisFooterStatus) -> None:
        self._status = status
        self.notify('progress-text')
        self.notify('save-enabled')
        self.notify('stop-visible')
        self.notify('previous-visible')
        self.notify('time-count')

    @GObject.Property(type=str, flags=GObject.ParamFlags.READABLE)
    def progress_text(self) -> str:
        if self._status is AnalysisFooterStatus.FINISHED:
            return 'Finished'
        elif self._status is AnalysisFooterStatus.CANCELLED:
            return 'Cancelled'
        else:
            return ''

    @GObject.Property(type=bool, default=False, flags=GObject.ParamFlags.READABLE)
    def save_enabled(self) -> bool:
        return self._status is not AnalysisFooterStatus.IN_PROGRESS

    @GObject.Property(type=bool, default=True, flags=GObject.ParamFlags.READABLE)
    def stop_visible(self) -> bool:
        return self._status is AnalysisFooterStatus.IN_PROGRESS

    @GObject.Property(type=bool, default=False, flags=GObject.ParamFlags.READABLE)
    def previous_visible(self) -> bool:
        return self._status is not AnalysisFooterStatus.IN_PROGRESS

    @GObject.Property(type=bool, default=True, flags=GObject.ParamFlags.READABLE)
    def time_count(self) -> bool:
        return self._status is AnalysisFooterStatus.IN_PROGRESS

    @install
    @GObject.Property(type=float)
    def progress(self) -> float:
        return self._progress

    @progress.setter
    def progress(self, progress: float) -> None:
        self._progress = progress

    @install
    @GObject.Property
    def time_start(self) -> Optional[float]:
        return self._time_start

    @time_start.setter
    def time_start(self, time_start: Optional[float]) -> None:
        self._time_start = time_start

    @install
    @GObject.Property
    def time_complete(self) -> Optional[float]:
        return self._time_complete

    @time_complete.setter
    def time_complete(self, time_complete: Optional[float]) -> None:
        self._time_complete = time_complete

    @install
    @GObject.Signal
    def save(self) -> None:
        pass

    @install
    @GObject.Signal
    def stop(self) -> None:
        pass

    @install
    @GObject.Signal
    def previous(self) -> None:
        pass

    def save_clicked(self, *_) -> None:
        self.emit('save')

    def stop_clicked(self, *_) -> None:
        self.emit('stop')

    def previous_clicked(self, *_) -> None:
        self.emit('previous')
