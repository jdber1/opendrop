from enum import Enum
from typing import Iterable, Sequence

from gi.repository import GObject

from opendrop.app.conan.analysis import ConanAnalysis


class ConanAnalysisProgressHelper(GObject.Object):
    class Status(Enum):
        ANALYSING = 0
        FINISHED  = 1
        CANCELLED = 2

    class _AnalysisWatcher:
        def __init__(self, analysis: ConanAnalysis, owner: 'ConanAnalysisProgressHelper') -> None:
            self.analysis = analysis
            self.owner = owner
            self._cleanup_tasks = []

            event_connections = [
                self.analysis.bn_status.on_changed.connect(
                    lambda: owner.notify('status'), weak_ref=False,
                ),
                self.analysis.bn_is_done.on_changed.connect(
                    lambda: owner.notify('fraction'), weak_ref=False,
                ),
                self.analysis.bn_time_start.on_changed.connect(
                    lambda: owner.notify('time-start'), weak_ref=False,
                ),
                self.analysis.bn_time_est_complete.on_changed.connect(
                    lambda: owner.notify('est-complete'), weak_ref=False,
                ),
            ]

            self._cleanup_tasks.extend(conn.disconnect for conn in event_connections)

        def destroy(self) -> None:
            for f in self._cleanup_tasks:
                f()

    def __init__(self, **properties) -> None:
        self._analyses = ()
        self._watchers = []
        super().__init__(**properties)

    @GObject.Property
    def analyses(self) -> Sequence[ConanAnalysis]:
        return self._analyses

    @analyses.setter
    def analyses(self, analyses: Iterable[ConanAnalysis]) -> None:
        self._analyses = tuple(analyses)
        self._update_watchers()

    def _update_watchers(self) -> None:
        analyses = self._analyses
        watching = [watcher.analysis for watcher in self._watchers]

        to_watch = set(analyses) - set(watching)
        for analysis in to_watch:
            self._watchers.append(self._AnalysisWatcher(analysis, self))

        to_unwatch = set(watching) - set(analyses)
        for analysis in to_unwatch:
            for w in tuple(self._watchers):
                if w.analysis == analysis:
                    self._watchers.remove(w)
                    w.destroy()

        self.notify('status')
        self.notify('fraction')
        self.notify('time-start')
        self.notify('est-complete')

    @GObject.Property
    def status(self) -> Status:
        analyses = self._analyses

        is_cancelled = any(
            analysis.bn_is_cancelled.get()
            for analysis in analyses
        )
        if is_cancelled:
            return self.Status.CANCELLED

        is_finished = all(
            analysis.bn_is_done.get() and not analysis.bn_is_cancelled.get()
            for analysis in analyses
        )
        if is_finished:
            return self.Status.FINISHED

        return self.Status.ANALYSING

    @GObject.Property(type=float)
    def time_start(self) -> float:
        analyses = self._analyses
        if not analyses: return 0.0

        time_start = min(
            analysis.bn_time_start.get()
            for analysis in analyses
        )

        return time_start

    @GObject.Property(type=float)
    def est_complete(self) -> float:
        analyses = self._analyses
        if not analyses: return 0.0

        time_est_complete = max(
            analysis.bn_time_est_complete.get()
            for analysis in analyses
        )

        return time_est_complete

    @GObject.Property(type=float)
    def fraction(self) -> float:
        analyses = self._analyses
        if not analyses: return 1.0

        num_completed = len([
            analysis
            for analysis in analyses
            if analysis.bn_is_done.get()
        ])

        completed_fraction = num_completed/len(analyses)

        return completed_fraction

    def calculate_time_elapsed(self) -> float:
        analyses = self._analyses
        if not analyses: return 0.0

        time_elapsed = max(
            analysis.calculate_time_elapsed()
            for analysis in analyses
        )

        return time_elapsed

    def calculate_time_remaining(self) -> float:
        analyses = self._analyses
        if not analyses: return 0.0

        time_remaining = max(
            analysis.calculate_time_remaining()
            for analysis in analyses
        )

        return time_remaining
