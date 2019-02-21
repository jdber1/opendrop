from operator import attrgetter
from typing import Optional, Sequence, MutableSequence, Callable

import numpy as np

from opendrop.utility.bindable import AtomicBindableAdapter, AtomicBindableVar, AtomicBindable
from .analyser import ConanAnalysis, ConanDropAnalysis


class ConanResultsExplorer:
    class SummaryData:
        def __init__(self, drops: Sequence[ConanDropAnalysis]) -> None:
            self.__destroyed = False
            self.__cleanup_tasks = []  # type: MutableSequence[Callable]

            self._drops = []  # type: MutableSequence[ConanDropAnalysis]

            self.bn_left_angle_data = AtomicBindableAdapter(self._get_left_angle_data)
            self.bn_right_angle_data = AtomicBindableAdapter(self._get_right_angle_data)

            self._track_drops(drops)

        def _get_left_angle_data(self) -> Sequence[float]:
            mask = np.isfinite(self._get_drop_timestamps())
            return np.array([(drop.image_timestamp, drop.bn_left_angle.get()) for drop in self._drops])[mask]

        def _get_right_angle_data(self) -> Sequence[float]:
            mask = np.isfinite(self._get_drop_timestamps())
            return np.array([(drop.image_timestamp, drop.bn_right_angle.get()) for drop in self._drops])[mask]

        def _get_drop_timestamps(self) -> Sequence[float]:
            return tuple(drop.image_timestamp for drop in self._drops)

        def _poke_all_data(self) -> None:
            self.bn_left_angle_data.poke()
            self.bn_right_angle_data.poke()

        def _track_drops(self, drops: Sequence[ConanDropAnalysis]) -> None:
            for drop in drops:
                self._track_drop(drop)

        def _track_drop(self, drop: ConanDropAnalysis) -> None:
            self._drops.append(drop)
            event_connections = [
                drop.bn_image_timestamp.on_changed.connect(self._poke_all_data),
                drop.bn_left_angle.on_changed.connect(self.bn_left_angle_data.poke),
                drop.bn_right_angle.on_changed.connect(self.bn_right_angle_data.poke)]
            self.__cleanup_tasks.extend(ec.disconnect for ec in event_connections)

        def destroy(self) -> None:
            assert not self.__destroyed
            for f in self.__cleanup_tasks:
                f()
            self.__destroyed = True

    def __init__(self):
        self._analysis = None
        self.bn_analysis = AtomicBindableAdapter(getter=lambda: self._analysis, setter=self._set_analysis)  # type: AtomicBindable[Optional[(IFTAnalysis)]]
        self.bn_individual_drops = AtomicBindableVar(tuple())  # type: AtomicBindable[Sequence[ConanDropAnalysis]]
        self.bn_summary_data = AtomicBindableVar(None)  # type: AtomicBindable[Optional[ConanResultsExplorer.SummaryData]]

    analysis = AtomicBindable.property_adapter(attrgetter('bn_analysis'))  # type: Optional[ConanAnalysis]
    individual_drops = AtomicBindable.property_adapter(attrgetter('bn_individual_drops'))  # type: Sequence[ConanDropAnalysis]
    summary_data = AtomicBindable.property_adapter(attrgetter('bn_summary_data'))  # type: SummaryData

    def _set_analysis(self, analysis: Optional[ConanAnalysis]) -> None:
        self._analysis = analysis

        if self.summary_data is not None:
            self.summary_data.destroy()
            self.summary_data = None

        if analysis is not None:
            self.individual_drops = tuple(self._analysis.drop_analyses)
            self.summary_data = self.SummaryData(self._analysis.drop_analyses)
        else:
            self.individual_drops = tuple()
