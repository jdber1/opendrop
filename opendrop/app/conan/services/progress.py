from enum import Enum
from typing import Iterable, Sequence, Optional

from gi.repository import GObject

from .analysis import ConanAnalysisJob


class ConanAnalysisProgressHelper(GObject.Object):
    class Status(Enum):
        ANALYSING = 0
        FINISHED  = 1
        CANCELLED = 2

    class _AnalysisWatcher:
        def __init__(self, analysis: ConanAnalysisJob, owner: 'ConanAnalysisProgressHelper') -> None:
            self.analysis = analysis
            self.owner = owner
            self._cleanup_tasks = []

            self._status_changed_id = analysis.connect('notify::status', self._status_changed)

        def _status_changed(self, *_) -> None:
            self.owner._analysis_status_changed(self)

        def destroy(self) -> None:
            self.analysis.disconnect(self._status_changed_id)

    def __init__(self, **properties) -> None:
        self._analyses = ()
        self._watchers = []
        super().__init__(**properties)

    @GObject.Property
    def analyses(self) -> Sequence[ConanAnalysisJob]:
        return self._analyses

    @analyses.setter
    def analyses(self, analyses: Iterable[ConanAnalysisJob]) -> None:
        self._analyses = tuple(analyses)
        self._update_watchers()

    def _update_watchers(self) -> None:
        analyses = self._analyses
        watching = [watcher.analysis for watcher in self._watchers]

        unwatch = set(watching) - set(analyses)
        watch = set(analyses) - set(watching)

        for analysis in unwatch:
            for w in tuple(self._watchers):
                if w.analysis == analysis:
                    self._watchers.remove(w)
                    w.destroy()

        for analysis in watch:
            self._watchers.append(self._AnalysisWatcher(analysis, self))

        self.notify('status')
        self.notify('fraction')
        self.notify('time-start')

    def _analysis_status_changed(self, *_) -> None:
        self.notify('status')
        self.notify('fraction')
        self.notify('time-start')

    @GObject.Property
    def status(self) -> Status:
        analyses = self._analyses

        if any(analysis.cancelled() for analysis in analyses):
            return self.Status.CANCELLED
        elif all(analysis.done() and not analysis.cancelled()
                 for analysis in analyses):
            return self.Status.FINISHED
        else:
            return self.Status.ANALYSING

    @GObject.Property
    def time_start(self) -> Optional[float]:
        analyses = self._analyses
        if not analyses: return None

        time_start = min(
            analysis.job_start
            for analysis in analyses
        )

        return time_start

    @GObject.Property(type=float)
    def fraction(self) -> float:
        analyses = self._analyses
        if not analyses: return 1.0

        num_completed = len([
            analysis
            for analysis in analyses
            if analysis.done()
        ])

        completed_fraction = num_completed/len(analyses)

        return completed_fraction
