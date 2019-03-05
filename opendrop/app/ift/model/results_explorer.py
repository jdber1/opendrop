from typing import Optional, Sequence, MutableSequence, Callable, Tuple

import numpy as np

from opendrop.app.ift.model.analyser import IFTAnalysis, IFTDropAnalysis
from opendrop.utility.simplebindable import Bindable, BoxBindable, AccessorBindable


class IFTResultsExplorer:
    class SummaryData:
        def __init__(self, drops: Sequence[IFTDropAnalysis]) -> None:
            self.__destroyed = False
            self.__cleanup_tasks = []  # type: MutableSequence[Callable]

            self._drops = []  # type: MutableSequence[IFTDropAnalysis]

            self.bn_ift_data = AccessorBindable(lambda: self.ift_data)
            self.bn_volume_data = AccessorBindable(lambda: self.volume_data)
            self.bn_surface_area_data = AccessorBindable(lambda: self.surface_area_data)

            self._track_drops(drops)

        def _track_drops(self, drops: Sequence[IFTDropAnalysis]) -> None:
            for drop in drops:
                self._track_drop(drop)

        def _track_drop(self, drop: IFTDropAnalysis) -> None:
            self._drops.append(drop)
            event_connections = [
                drop.bn_image_timestamp.on_changed.connect(self._poke_all_data),
                drop.bn_interfacial_tension.on_changed.connect(self.bn_ift_data.poke),
                drop.bn_volume.on_changed.connect(self.bn_volume_data.poke),
                drop.bn_surface_area.on_changed.connect(self.bn_surface_area_data.poke)]
            self.__cleanup_tasks.extend(ec.disconnect for ec in event_connections)

        def _poke_all_data(self) -> None:
            self.bn_ift_data.poke()
            self.bn_volume_data.poke()
            self.bn_surface_area_data.poke()

        @property
        def ift_data(self) -> Sequence[Tuple[float, float]]:
            mask = np.isfinite(self._get_drop_timestamps())
            return np.array([(drop.image_timestamp, drop.interfacial_tension) for drop in self._drops])[mask]

        @property
        def volume_data(self) -> Sequence[Tuple[float, float]]:
            mask = np.isfinite(self._get_drop_timestamps())
            return np.array([(drop.image_timestamp, drop.volume) for drop in self._drops])[mask]

        @property
        def surface_area_data(self) -> Sequence[Tuple[float, float]]:
            mask = np.isfinite(self._get_drop_timestamps())
            return np.array([(drop.image_timestamp, drop.surface_area) for drop in self._drops])[mask]

        def _get_drop_timestamps(self) -> Sequence[float]:
            return tuple(drop.image_timestamp for drop in self._drops)

        def destroy(self) -> None:
            assert not self.__destroyed
            for f in self.__cleanup_tasks:
                f()
            self.__destroyed = True

    def __init__(self):
        self._analysis = None
        self.bn_analysis = AccessorBindable(getter=lambda: self._analysis, setter=self._set_analysis)  # type: Bindable[Optional[(IFTAnalysis)]]
        self.bn_individual_drops = BoxBindable(tuple())  # type: Bindable[Sequence[IFTDropAnalysis]]
        self.bn_summary_data = BoxBindable(None)  # type: Bindable[Optional[IFTResultsExplorer.SummaryData]]

    @property
    def analysis(self) -> Optional[IFTAnalysis]:
        return self.bn_analysis.get()

    @analysis.setter
    def analysis(self, new_analysis: Optional[IFTAnalysis]) -> None:
        self.bn_analysis.set(new_analysis)

    @property
    def individual_drops(self) -> Sequence[IFTDropAnalysis]:
        return self.bn_individual_drops.get()

    @individual_drops.setter
    def individual_drops(self, new_drops: Sequence[IFTDropAnalysis]) -> None:
        self.bn_individual_drops.set(new_drops)

    @property
    def summary_data(self) -> SummaryData:
        return self.bn_summary_data.get()

    @summary_data.setter
    def summary_data(self, new_data: SummaryData) -> None:
        self.bn_summary_data.set(new_data)

    def _set_analysis(self, analysis: Optional[IFTAnalysis]) -> None:
        self._analysis = analysis

        if self.summary_data is not None:
            self.summary_data.destroy()
            self.summary_data = None

        if analysis is not None:
            self.individual_drops = tuple(self._analysis.drop_analyses)
            self.summary_data = self.SummaryData(self._analysis.drop_analyses)
        else:
            self.individual_drops = tuple()
