import functools
from typing import Sequence, Optional

from opendrop.utility.bindable.bindable import AtomicBindable


class MutuallyExclusiveOptions:
    def __init__(self, options: Sequence[AtomicBindable[bool]]) -> None:
        self._options = options
        self._current_active_switch = None  # type: Optional[Switch]
        self._cleanup_tasks = []

        for option in self._options:
            if option.get() is True:
                raise ValueError('Must be initialised with all options initially False')
            ec = option.on_changed.connect(functools.partial(self._hdl_option_changed, option),
                                           strong_ref=True, immediate=True)
            self._cleanup_tasks.append(ec.disconnect)

    def _hdl_option_changed(self, option: AtomicBindable[bool]) -> None:
        if option.get() is False:
            return
        # Disable the other options
        for other_option in self._options:
            if other_option is option:
                continue
            if other_option.get() is True:
                other_option.set(False)

    def destroy(self) -> None:
        for f in self._cleanup_tasks:
            f()

        self._cleanup_tasks = []
