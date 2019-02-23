from operator import attrgetter
from typing import Callable

from opendrop.app.common.footer import AnalysisFooterModel, AnalysisFooterStatus
from opendrop.app.ift.model.analyser import IFTAnalysis
from opendrop.utility.bindable.bindable import AtomicBindableAdapter, AtomicBindable


class IFTAnalysisFooterModel(AnalysisFooterModel):
    def __init__(self,
                 analysis: IFTAnalysis,
                 back_action: Callable,
                 cancel_action: Callable,
                 save_action: Callable) -> None:

        self._analysis = analysis
        self.__destroyed = False
        self.__cleanup_tasks = []

        self._back_action = back_action
        self._cancel_action = cancel_action
        self._save_action = save_action

        self.bn_status = AtomicBindableAdapter(getter=self._get_status)  # type: AtomicBindableAdapter[AnalysisFooterStatus]
        self.bn_time_start = analysis.bn_time_start
        self.bn_time_est_complete = analysis.bn_time_est_complete
        self.bn_progress_fraction = analysis.bn_progress

        event_connections = [
            analysis.bn_progress.on_changed.connect(self.bn_status.poke),
            analysis.bn_cancelled.on_changed.connect(self.bn_status.poke)]
        self.__cleanup_tasks.extend(ec.disconnect for ec in event_connections)

    status = AtomicBindable.property_adapter(attrgetter('bn_status'))  # type: AnalysisFooterStatus
    time_start = AtomicBindable.property_adapter(attrgetter('bn_time_start'))  # type: float
    time_est_complete = AtomicBindable.property_adapter(attrgetter('bn_time_est_complete'))  # type: float
    progress_fraction = AtomicBindable.property_adapter(attrgetter('bn_progress_fraction'))  # type: float

    def back(self) -> None:
        self._back_action()

    def cancel(self) -> None:
        self._cancel_action()

    def save(self) -> None:
        self._save_action()

    def _get_status(self) -> AnalysisFooterStatus:
        cancelled = self._analysis.bn_cancelled.get()
        if cancelled:
            return AnalysisFooterStatus.CANCELLED

        all_done = all(d.status.terminal for d in self._analysis.drop_analyses)
        if all_done:
            return AnalysisFooterStatus.FINISHED

        return AnalysisFooterStatus.IN_PROGRESS

    def destroy(self) -> None:
        assert not self.__destroyed
        for f in self.__cleanup_tasks:
            f()
        self.__destroyed = True
