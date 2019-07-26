import math
from typing import Sequence

from opendrop.app.ift.analysis import IFTDropAnalysis
from opendrop.utility.bindable import Bindable, BoxBindable


class GraphsModel:
    def __init__(self, in_analyses: Bindable[Sequence[IFTDropAnalysis]]) -> None:
        self._bn_analyses = in_analyses

        self._tracked_analyses = []
        self._tracked_analysis_unbind_tasks = {}

        self.bn_ift_data = BoxBindable((tuple(), tuple()))
        self.bn_volume_data = BoxBindable((tuple(), tuple()))
        self.bn_surface_area_data = BoxBindable((tuple(), tuple()))

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

    def _track_analysis(self, analysis: IFTDropAnalysis) -> None:
        unbind_tasks = []

        event_connections = [
            analysis.bn_interfacial_tension.on_changed.connect(
                self._hdl_tracked_analysis_data_changed
            ),
            analysis.bn_volume.on_changed.connect(
                self._hdl_tracked_analysis_data_changed
            ),
            analysis.bn_surface_area.on_changed.connect(
                self._hdl_tracked_analysis_data_changed
            ),
        ]

        unbind_tasks.extend(
            ec.disconnect for ec in event_connections
        )

        self._tracked_analyses.append(analysis)
        self._tracked_analysis_unbind_tasks[analysis] = unbind_tasks

        self._hdl_tracked_analysis_data_changed()

    def _untrack_analysis(self, analysis: IFTDropAnalysis) -> None:
        unbind_tasks = self._tracked_analysis_unbind_tasks[analysis]
        for task in unbind_tasks:
            task()

        del self._tracked_analysis_unbind_tasks[analysis]
        self._tracked_analyses.remove(analysis)

    def _hdl_tracked_analysis_data_changed(self) -> None:
        ift_data = []
        vol_data = []
        sur_data = []

        analyses = self._bn_analyses.get()

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

        self.bn_ift_data.set(ift_data)
        self.bn_volume_data.set(vol_data)
        self.bn_surface_area_data.set(sur_data)
