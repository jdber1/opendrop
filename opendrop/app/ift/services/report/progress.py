from enum import Enum
import math

from gi.repository import GObject
from injector import inject

from opendrop.app.ift.analysis import IFTDropAnalysis

from . import IFTReportService


class IFTReportProgressService(GObject.Object):
    class Status(Enum):
        NO_ANALYSES = 0
        FITTING = 1
        FINISHED = 2
        CANCELLED = 3

    class _AnalysisWatcher:
        def __init__(self, analysis: IFTDropAnalysis, owner: 'IFTReportProgressService') -> None:
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

    @inject
    def __init__(self, report: IFTReportService) -> None:
        self._report = report
        self._watchers = []

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
            for w in watching:
                if w.analysis == analysis:
                    self._watchers.remove(w)
                    w.destroy()

    @GObject.Property
    def status(self) -> Status:
        analyses = self._report.bn_analyses.get()

        if len(analyses) == 0:
            return self.Status.NO_ANALYSES

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

        return self.Status.FITTING

    @GObject.Property(type=float)
    def time_start(self) -> float:
        analyses = self._report.bn_analyses.get()
        if len(analyses) == 0:
            return math.nan

        time_start = min(
            analysis.bn_time_start.get()
            for analysis in analyses
        )

        return time_start

    @GObject.Property(type=float)
    def est_complete(self) -> float:
        analyses = self._report.bn_analyses.get()
        if len(analyses) == 0:
            return math.nan

        time_est_complete = max(
            analysis.bn_time_est_complete.get()
            for analysis in analyses
        )

        return time_est_complete

    @GObject.Property(type=float)
    def fraction(self) -> float:
        analyses = self._report.bn_analyses.get()
        if len(analyses) == 0:
            return math.nan

        num_completed = len([
            analysis
            for analysis in analyses
            if analysis.bn_is_done.get()
        ])

        completed_fraction = num_completed/len(analyses)

        return completed_fraction

    def calculate_time_elapsed(self) -> float:
        analyses = self._report.bn_analyses.get()
        if len(analyses) == 0:
            return math.nan

        time_elapsed = max(
            analysis.calculate_time_elapsed()
            for analysis in analyses
        )

        return time_elapsed

    def calculate_time_remaining(self) -> float:
        analyses = self._report.bn_analyses.get()
        if len(analyses) == 0:
            return math.nan

        time_remaining = max(
            analysis.calculate_time_remaining()
            for analysis in analyses
        )

        return time_remaining
