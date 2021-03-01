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


from typing import Sequence, Iterable, Tuple

from gi.repository import GObject
import numpy as np

from opendrop.app.conan.services.analysis import ConanAnalysisJob


class ConanReportGraphsService(GObject.Object):
    _analyses: Sequence[ConanAnalysisJob] = ()
    _left_angle: Tuple[Sequence[float], Sequence[float]] = np.empty((2, 0))
    _right_angle: Tuple[Sequence[float], Sequence[float]] = np.empty((2, 0))

    class _AnalysisWatcher:
        def __init__(self, analysis: ConanAnalysisJob, owner: 'ConanReportGraphsService') -> None:
            self.analysis = analysis
            self._owner = owner
            self._cleanup_tasks = []

            self._handler_ids = [
                self.analysis.connect('notify::left-angle', owner._analysis_data_changed),
                self.analysis.connect('notify::right-angle', owner._analysis_data_changed),
            ]

        def destroy(self) -> None:
            for hid in self._handler_ids:
                self.analysis.disconnect(hid)

    def __init__(self, **properties) -> None:
        self._watchers = []
        super().__init__(**properties)

    @GObject.Property
    def analyses(self) -> Sequence[ConanAnalysisJob]:
        return self._analyses

    @analyses.setter
    def analyses(self, value: Iterable[ConanAnalysisJob]) -> None:
        self._analyses = tuple(value)
        self._analyses_changed()

    @GObject.Property
    def left_angle(self) -> Tuple[Sequence[float], Sequence[float]]:
        return self._left_angle

    @GObject.Property
    def right_angle(self) -> Tuple[Sequence[float], Sequence[float]]:
        return self._right_angle

    def _analyses_changed(self) -> None:
        analyses = self._analyses
        watchers = self._watchers
        watching = {w.analysis for w in watchers}

        for a in analyses:
            if a not in watching:
                self._watchers.append(self._AnalysisWatcher(a, self))

        for w in watchers:
            if w.analysis not in analyses:
                w.destroy()
                self._watchers.remove(w)

        self._analysis_data_changed()

    def _analysis_data_changed(self, *_) -> None:
        left_angle_data = []
        right_angle_data = []

        analyses = self._analyses

        for analysis in analyses:
            timestamp = analysis.timestamp
            if timestamp is None: continue

            left_angle = analysis.left_angle
            right_angle = analysis.right_angle

            if left_angle is not None:
                left_angle_data.append([timestamp, left_angle])

            if right_angle is not None:
                right_angle_data.append([timestamp, right_angle])

        # Sort in ascending order of timestamp.
        left_angle_data = sorted(left_angle_data, key=lambda p: p[0])
        right_angle_data = sorted(right_angle_data, key=lambda p: p[0])

        # Transpose data.
        if len(left_angle_data) > 0:
            left_angle_data = tuple(zip(*left_angle_data))
        else:
            left_angle_data = ((), ())
        if len(right_angle_data) > 0:
            right_angle_data = tuple(zip(*right_angle_data))
        else:
            right_angle_data = ((), ())

        self._left_angle = np.array(left_angle_data)
        self._right_angle = np.array(right_angle_data)

        self.notify('left-angle')
        self.notify('right-angle')
