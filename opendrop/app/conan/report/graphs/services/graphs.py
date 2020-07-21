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
from typing import Sequence, Iterable, Tuple

from gi.repository import GObject

from opendrop.app.conan.analysis import ConanAnalysis


class ConanReportGraphsService(GObject.Object):
    _analyses = ()  # type: Sequence[ConanAnalysis]
    _left_angle = ((), ())  # type: Tuple[Sequence[float], Sequence[float]]
    _right_angle = ((), ())  # type: Tuple[Sequence[float], Sequence[float]]

    class _AnalysisWatcher:
        def __init__(self, analysis: ConanAnalysis, owner: 'ConanReportGraphsService') -> None:
            self.analysis = analysis
            self._owner = owner
            self._cleanup_tasks = []

            event_connections = [
                self.analysis.bn_left_angle.on_changed.connect(
                    owner._tracked_analysis_data_changed
                ),
                self.analysis.bn_right_angle.on_changed.connect(
                    owner._tracked_analysis_data_changed
                ),
            ]

            self._cleanup_tasks.extend(conn.disconnect for conn in event_connections)

        def destroy(self) -> None:
            for f in self._cleanup_tasks:
                f()

    def __init__(self, **properties) -> None:
        self._watchers = []
        super().__init__(**properties)

    @GObject.Property
    def analyses(self) -> Sequence[ConanAnalysis]:
        return self._analyses

    @analyses.setter
    def analyses(self, value: Iterable[ConanAnalysis]) -> None:
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
        watching = [w.analysis for w in self._watchers]

        to_watch = set(analyses) - set(watching)
        for analysis in to_watch:
            self._watchers.append(self._AnalysisWatcher(analysis, self))

        to_unwatch = set(watching) - set(analyses)
        for analysis in to_unwatch:
            for w in tuple(self._watchers):
                if w.analysis == analysis:
                    w.destroy()
                    self._watchers.remove(w)

        self._tracked_analysis_data_changed()

    def _tracked_analysis_data_changed(self) -> None:
        left_angle_data = []
        right_angle_data = []

        analyses = self._analyses

        for analysis in analyses:
            timestamp = analysis.bn_image_timestamp.get()
            if timestamp is None or not math.isfinite(timestamp):
                continue

            left_angle_value = analysis.bn_left_angle.get()
            right_angle_value = analysis.bn_right_angle.get()

            if left_angle_value is not None and math.isfinite(left_angle_value):
                left_angle_data.append((timestamp, left_angle_value))

            if right_angle_value is not None and math.isfinite(right_angle_value):
                right_angle_data.append((timestamp, right_angle_value))

        # Sort in ascending order of timestamp
        left_angle_data = sorted(left_angle_data, key=lambda x: x[0])
        right_angle_data = sorted(right_angle_data, key=lambda x: x[0])

        left_angle_data = tuple(zip(*left_angle_data))
        right_angle_data = tuple(zip(*right_angle_data))

        if len(left_angle_data) == 0:
            left_angle_data = (tuple(), tuple())

        if len(right_angle_data) == 0:
            right_angle_data = (tuple(), tuple())

        self._left_angle = left_angle_data
        self._right_angle = right_angle_data

        self.notify('left-angle')
        self.notify('right-angle')
