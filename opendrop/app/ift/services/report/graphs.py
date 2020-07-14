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
from typing import Tuple, Sequence

from gi.repository import GObject

from . import IFTReportService
from opendrop.app.ift.analysis import IFTDropAnalysis
from opendrop.appfw import inject


class IFTReportGraphsService(GObject.Object):
    class _AnalysisWatcher:
        def __init__(self, analysis: IFTDropAnalysis, owner: 'IFTReportGraphsService') -> None:
            self.analysis = analysis
            self._owner = owner
            self._cleanup_tasks = []

            event_connections = [
                self.analysis.bn_interfacial_tension.on_changed.connect(
                    owner._hdl_tracked_analysis_data_changed
                ),
                self.analysis.bn_volume.on_changed.connect(
                    owner._hdl_tracked_analysis_data_changed
                ),
                self.analysis.bn_surface_area.on_changed.connect(
                    owner._hdl_tracked_analysis_data_changed
                ),
            ]

            self._cleanup_tasks.extend(conn.disconnect for conn in event_connections)

        def destroy(self) -> None:
            for f in self._cleanup_tasks:
                f()

    @inject
    def __init__(self, report: IFTReportService) -> None:
        super().__init__()
        self._report = report
        self._watchers = []

        self._ift = ((), ())  # type: Tuple[Sequence[float], Sequence[float]]
        self._volume = ((), ())  # type: Tuple[Sequence[float], Sequence[float]]
        self._surface_area = ((), ())  # type: Tuple[Sequence[float], Sequence[float]]

        self._report.bn_analyses.on_changed.connect(self._hdl_analyses_changed)
        self._hdl_analyses_changed()

    def _hdl_analyses_changed(self) -> None:
        analyses = self._report.bn_analyses.get()
        watching = [watcher.analysis for watcher in self._watchers]

        to_watch = set(analyses) - set(watching)
        for analysis in to_watch:
            self._watchers.append(self._AnalysisWatcher(analysis, self))

        to_unwatch = set(watching) - set(analyses)
        for analysis in to_unwatch:
            for watcher in self._watchers:
                if watcher.analysis == analysis:
                    self._watchers.remove(watcher)
                    watcher.destroy()

        self._hdl_tracked_analysis_data_changed()

    def _hdl_tracked_analysis_data_changed(self) -> None:
        ift_data = []
        vol_data = []
        sur_data = []

        analyses = self._report.bn_analyses.get()

        for analysis in analyses:
            timestamp = analysis.bn_image_timestamp.get()
            if timestamp is None or not math.isfinite(timestamp):
                continue

            ift_value = analysis.bn_interfacial_tension.get()
            vol_value = analysis.bn_volume.get()
            sur_value = analysis.bn_surface_area.get()

            if ift_value is not None and math.isfinite(ift_value):
                ift_data.append((timestamp, ift_value))

            if vol_value is not None and math.isfinite(vol_value):
                vol_data.append((timestamp, vol_value))

            if sur_value is not None and math.isfinite(sur_value):
                sur_data.append((timestamp, sur_value))

        # Sort in ascending order of timestamp
        ift_data = sorted(ift_data, key=lambda x: x[0])
        vol_data = sorted(vol_data, key=lambda x: x[0])
        sur_data = sorted(sur_data, key=lambda x: x[0])

        ift_data = tuple(zip(*ift_data))
        vol_data = tuple(zip(*vol_data))
        sur_data = tuple(zip(*sur_data))

        if len(ift_data) == 0:
            ift_data = (tuple(), tuple())

        if len(vol_data) == 0:
            vol_data = (tuple(), tuple())

        if len(sur_data) == 0:
            sur_data = (tuple(), tuple())

        self._ift = ift_data
        self._volume = vol_data
        self._surface_area = sur_data

        self.notify('ift')
        self.notify('volume')
        self.notify('surface-area')

    @GObject.Property
    def ift(self) -> Tuple[Sequence[float], Sequence[float]]:
        return self._ift

    @GObject.Property
    def volume(self) -> Tuple[Sequence[float], Sequence[float]]:
        return self._volume

    @GObject.Property
    def surface_area(self) -> Tuple[Sequence[float], Sequence[float]]:
        return self._surface_area
