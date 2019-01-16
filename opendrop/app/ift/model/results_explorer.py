from operator import attrgetter
from typing import Optional, Sequence, MutableSequence, Callable, Tuple

import numpy as np

from opendrop.app.ift.model.analyser import IFTAnalysis, IFTDropAnalysis
from opendrop.utility.bindable.bindable import AtomicBindable, AtomicBindableVar, AtomicBindableAdapter


class IFTResultsExplorer:
    class SummaryData:
        def __init__(self, drops: Sequence[IFTDropAnalysis]) -> None:
            self.__destroyed = False
            self.__cleanup_tasks = []  # type: MutableSequence[Callable]

            self._drops = []  # type: MutableSequence[IFTDropAnalysis]

            self.bn_ift_data = AtomicBindableAdapter(self._get_ift_data)
            self.bn_volume_data = AtomicBindableAdapter(self._get_volume_data)
            self.bn_surface_area_data = AtomicBindableAdapter(self._get_surface_area_data)

            self._track_drops(drops)

        ift_data = AtomicBindable.property_adapter(attrgetter('bn_ift_data'))  # type: Sequence[Tuple[float, float]]
        volume_data = AtomicBindable.property_adapter(attrgetter('bn_volume_data'))  # type: Sequence[Tuple[float, float]]
        surface_area_data = AtomicBindable.property_adapter(attrgetter('bn_surface_area_data'))  # type: Sequence[Tuple[float, float]]

        def _poke_all_data(self) -> None:
            self.bn_ift_data.poke()
            self.bn_volume_data.poke()
            self.bn_surface_area_data.poke()

        def _track_drops(self, drops: Sequence[IFTDropAnalysis]) -> None:
            for drop in drops:
                self._track_drop(drop)

        def _track_drop(self, drop: IFTDropAnalysis) -> None:
            self._drops.append(drop)
            event_connections = [
                drop.bn_image_timestamp.on_changed.connect(self._poke_all_data, immediate=True),
                drop.bn_interfacial_tension.on_changed.connect(self.bn_ift_data.poke, immediate=True),
                drop.bn_volume.on_changed.connect(self.bn_volume_data.poke, immediate=True),
                drop.bn_surface_area.on_changed.connect(self.bn_surface_area_data.poke, immediate=True)]
            self.__cleanup_tasks.extend(ec.disconnect for ec in event_connections)

        def _get_drop_timestamps(self) -> Sequence[float]:
            return tuple(drop.image_timestamp for drop in self._drops)

        def _get_ift_data(self) -> Sequence[Tuple[float, float]]:
            mask = np.isfinite(self._get_drop_timestamps())
            return np.array([(drop.image_timestamp, drop.interfacial_tension) for drop in self._drops])[mask]

        def _get_volume_data(self) -> Sequence[Tuple[float, float]]:
            mask = np.isfinite(self._get_drop_timestamps())
            return np.array([(drop.image_timestamp, drop.volume) for drop in self._drops])[mask]

        def _get_surface_area_data(self) -> Sequence[Tuple[float, float]]:
            mask = np.isfinite(self._get_drop_timestamps())
            return np.array([(drop.image_timestamp, drop.surface_area) for drop in self._drops])[mask]

        def destroy(self) -> None:
            assert not self.__destroyed
            for f in self.__cleanup_tasks:
                f()
            self.__destroyed = True

    def __init__(self):
        self._analysis = None
        self.bn_individual_drops = AtomicBindableVar(tuple())  # type: AtomicBindable[Sequence[IFTDropAnalysis]]
        self.bn_summary_data = AtomicBindableVar(None)  # type: AtomicBindable[Optional[IFTResultsExplorer.SummaryData]]

    individual_drops = AtomicBindable.property_adapter(attrgetter('bn_individual_drops'))  # type: Sequence[IFTDropAnalysis]
    summary_data = AtomicBindable.property_adapter(attrgetter('bn_summary_data'))  # type: IFTResultsExplorer.SummaryData

    analysis = property()

    @analysis.setter
    def analysis(self, analysis: IFTAnalysis) -> None:
        self._analysis = analysis

        self.individual_drops = tuple(self._analysis.drops)

        if self.summary_data is not None:
            self.summary_data.destroy()
            self.summary_data = None

        self.summary_data = self.SummaryData(self._analysis.drops)
