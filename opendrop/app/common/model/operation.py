from typing import Sequence

from opendrop.utility.bindable import Bindable, AccessorBindable, BoxBindable


class Operation:
    bn_done = None  # type: Bindable[bool]
    bn_cancelled = None  # type: Bindable[bool]
    bn_progress = None  # type: Bindable[float]
    bn_time_start = None  # type: Bindable[float]
    bn_time_est_complete = None  # type: Bindable[float]

    def cancel(self) -> None:
        pass


class OperationGroup(Operation):
    def __init__(self, operations: Sequence[Operation]) -> None:
        self._operations = operations

        self.bn_done = AccessorBindable(self._get_done)
        self.bn_cancelled = BoxBindable(False)
        self.bn_progress = AccessorBindable(self._get_progress)
        self.bn_time_start = AccessorBindable(self._get_time_start)
        self.bn_time_est_complete = AccessorBindable(self._get_time_est_complete)

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
        if self.bn_done.get():
            return

        for op in self._operations:
            if op.bn_done.get():
                continue
            op.cancel()

        self.bn_cancelled.set(True)
