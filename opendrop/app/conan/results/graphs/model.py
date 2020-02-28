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
from typing import Sequence

from opendrop.app.conan.analysis import ConanAnalysis
from opendrop.utility.bindable import VariableBindable
from opendrop.utility.bindable.typing import Bindable


class GraphsModel:
    def __init__(self, in_analyses: Bindable[Sequence[ConanAnalysis]]) -> None:
        self._bn_analyses = in_analyses

        self._tracked_analyses = []
        self._tracked_analysis_unbind_tasks = {}

        self.bn_left_angle_data = VariableBindable((tuple(), tuple()))
        self.bn_right_angle_data = VariableBindable((tuple(), tuple()))

        self._bn_analyses.on_changed.connect(
            self._hdl_analyses_changed
        )

        self._hdl_analyses_changed()

    def _hdl_analyses_changed(self) -> None:
        analyses = self._bn_analyses.get()
        tracked_analyses = self._tracked_analyses

        to_track = set(analyses) - set(tracked_analyses)
        for analysis in to_track:
            self._track_analysis(analysis)

        to_untrack = set(tracked_analyses) - set(analyses)
        for analysis in to_untrack:
            self._untrack_analysis(analysis)

    def _track_analysis(self, analysis: ConanAnalysis) -> None:
        unbind_tasks = []

        event_connections = [
            analysis.bn_left_angle.on_changed.connect(
                self._hdl_tracked_analysis_data_changed
            ),
            analysis.bn_right_angle.on_changed.connect(
                self._hdl_tracked_analysis_data_changed
            ),
        ]

        unbind_tasks.extend(
            ec.disconnect for ec in event_connections
        )

        self._tracked_analyses.append(analysis)
        self._tracked_analysis_unbind_tasks[analysis] = unbind_tasks

        self._hdl_tracked_analysis_data_changed()

    def _untrack_analysis(self, analysis: ConanAnalysis) -> None:
        unbind_tasks = self._tracked_analysis_unbind_tasks[analysis]
        for task in unbind_tasks:
            task()

        del self._tracked_analysis_unbind_tasks[analysis]
        self._tracked_analyses.remove(analysis)

    def _hdl_tracked_analysis_data_changed(self) -> None:
        left_angle_data = []
        right_angle_data = []

        analyses = self._bn_analyses.get()

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

        self.bn_left_angle_data.set(left_angle_data)
        self.bn_right_angle_data.set(right_angle_data)
