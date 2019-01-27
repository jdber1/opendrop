from typing import Sequence

from opendrop.utility.bindable import AtomicBindable, AtomicBindableAdapter


class Operation:
    bn_done = None  # type: AtomicBindable[bool]
    bn_progress = None  # type: AtomicBindable[float]
    bn_time_start = None  # type: AtomicBindable[float]
    bn_time_est_complete = None  # type: AtomicBindable[float]

    def cancel(self) -> None:
        pass


class OperationGroup(Operation):
    def __init__(self, operations: Sequence[Operation]) -> None:
        self._operations = operations

        self.bn_done = AtomicBindableAdapter(self._get_done)
        self.bn_progress = AtomicBindableAdapter(self._get_progress)
        self.bn_time_start = AtomicBindableAdapter(self._get_time_start)
        self.bn_time_est_complete = AtomicBindableAdapter(self._get_time_est_complete)

        for op in self._operations:
            op.bn_done.on_changed.connect(self.bn_done.poke)
            op.bn_progress.on_changed.connect(self.bn_progress.poke)
            op.bn_time_start.on_changed.connect(self.bn_time_start.poke)
            op.bn_time_est_complete.on_changed.connect(self.bn_time_est_complete.poke)

    def _get_done(self) -> bool:
        return all(op.bn_done.get() for op in self._operations)

    def _get_progress(self) -> bool:
        return sum(op.bn_progress.get() for op in self._operations)/len(self._operations)

    def _get_time_start(self) -> float:
        return min(op.bn_time_start.get() for op in self._operations)

    def _get_time_est_complete(self) -> bool:
        return max(op.bn_time_est_complete.get() for op in self._operations)

    def cancel(self) -> None:
        for op in self._operations:
            if op.bn_done.get():
                continue
            op.cancel()