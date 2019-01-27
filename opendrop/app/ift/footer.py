import math
from operator import attrgetter
from typing import Optional, MutableSequence, Callable

from opendrop.app.common.footer import AnalysisFooterModel, AnalysisFooterStatus
from opendrop.app.ift.model.analyser import IFTAnalysis
from opendrop.utility.bindable.bindable import AtomicBindableAdapter, AtomicBindable


class _IFTAnalysisFooterModel:
    def __init__(self, analysis: IFTAnalysis) -> None:
        self._analysis = analysis
        self.__destroyed = False
        self.__cleanup_tasks = []

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


class IFTAnalysisFooterModel(AnalysisFooterModel):
    def __init__(self, back_action: Callable, cancel_action: Callable, save_action: Callable) -> None:
        self._actual_model = None  # type: Optional[IFTAnalysis]
        self._actual_model_cleanup_tasks = []  # type: MutableSequence[Callable]

        self.bn_analysis = AtomicBindableAdapter(setter=self._set_analysis)

        self.bn_status = AtomicBindableAdapter(getter=self._get_status)  # type: AtomicBindableAdapter[AnalysisFooterStatus]
        self.bn_time_start = AtomicBindableAdapter(getter=self._get_time_start)  # type: AtomicBindableAdapter[float]
        self.bn_time_est_complete = AtomicBindableAdapter(getter=self._get_time_est_complete)  # type: AtomicBindableAdapter[float]
        self.bn_progress_fraction = AtomicBindableAdapter(getter=self._get_progress_fraction)  # type: AtomicBindableAdapter[float]

        self._back_action = back_action
        self._cancel_action = cancel_action
        self._save_action = save_action

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
        if self._actual_model is None:
            return AnalysisFooterStatus.IN_PROGRESS

        return self._actual_model.status

    def _get_time_start(self) -> float:
        if self._actual_model is None:
            return math.nan

        return self._actual_model.time_start

    def _get_time_est_complete(self) -> float:
        if self._actual_model is None:
            return math.nan

        return self._actual_model.time_est_complete

    def _get_progress_fraction(self) -> float:
        if self._actual_model is None:
            return 0

        return self._actual_model.progress_fraction

    def _destroy_current_actual_model(self) -> None:
        if self._actual_model is None:
            return

        self._actual_model.destroy()
        self._actual_model = None
        for f in self._actual_model_cleanup_tasks:
            f()
        self._actual_model_cleanup_tasks = []

    def _set_analysis(self, analysis: IFTAnalysis) -> None:
        self._destroy_current_actual_model()

        if analysis is None:
            return

        self._actual_model = _IFTAnalysisFooterModel(analysis)
        event_connections = [
            self._actual_model.bn_status.on_changed.connect(self.bn_status.poke),
            self._actual_model.bn_time_start.on_changed.connect(self.bn_time_start.poke),
            self._actual_model.bn_time_est_complete.on_changed.connect(self.bn_time_est_complete.poke),
            self._actual_model.bn_progress_fraction.on_changed.connect(self.bn_progress_fraction.poke)]
        self._actual_model_cleanup_tasks.extend(ec.disconnect for ec in event_connections)

        self.bn_status.poke()
        self.bn_time_start.poke()
        self.bn_time_est_complete.poke()
        self.bn_progress_fraction.poke()

    def destroy(self) -> None:
        self._destroy_current_actual_model()
