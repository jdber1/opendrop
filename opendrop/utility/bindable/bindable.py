import math
from abc import abstractmethod
from typing import Any
from typing import Generic, TypeVar, Callable, Optional

import numpy as np

from opendrop.utility.events import Event

_T = TypeVar('_T')


def _general_purpose_equality_check(x: Any, y: Any) -> bool:
    if isinstance(x, float) and isinstance(y, float):
        return math.isclose(x, y)

    # Use np.array_equal() in case x or y are `np.ndarray`'s, in which case `bool(x == y)` will throw:
    # > ValueError: The truth value of an array with more than one element is ambiguous...
    # Even if x and y aren't both `np.ndarray`'s, the implementation of np.array_equal() means that the result will
    # be identical to evaluating `x == y`, although this behaviour does not seem to be guaranteed by documentation.
    return np.array_equal(x, y)


class Bindable(Generic[_T]):
    def __init__(self, check_equals: Callable[[_T, _T], bool] = _general_purpose_equality_check) -> None:
        self.on_changed = Event()

        self._check_equals = check_equals

    def get(self) -> _T:
        return self._get_value()

    def set(self, new_value: _T) -> None:
        try:
            current_value = self.get()
        except NotImplementedError:
            pass
        else:
            if self._check_equals(current_value, new_value):
                return

        self._set_value(new_value)
        self.on_changed.fire()

    # Convenience methods for creating Bindings
    def bind(self, dst: 'Bindable[_T]') -> 'Binding':
        from .binding import Binding
        return Binding(src=self, dst=dst)

    def bind_to(self, dst: 'Bindable[_T]') -> 'Binding':
        from .binding import Binding
        return Binding(src=self, dst=dst, one_way=True)

    def bind_from(self, src: 'Bindable[_T]') -> 'Binding':
        from .binding import Binding
        return Binding(src=src, dst=self, one_way=True)

    @abstractmethod
    def _get_value(self) -> _T:
        """Actual implementation used to get the value"""
        raise NotImplementedError

    @abstractmethod
    def _set_value(self, new_value: _T) -> None:
        """Actual implementation used to set a new value"""
        raise NotImplementedError


class BoxBindable(Bindable[_T]):
    def __init__(self, initial: _T, **kwargs) -> None:
        super().__init__(**kwargs)

        self._value = initial

    def _get_value(self) -> _T:
        return self._value

    def _set_value(self, new_value: _T) -> None:
        self._value = new_value


class AccessorBindable(Bindable[_T]):
    def __init__(self, getter: Optional[Callable[[], _T]] = None, setter: Optional[Callable[[_T], None]] = None,
                 **kwargs) -> None:
        super().__init__(**kwargs)

        self._getter = getter
        self._setter = setter

    def poke(self) -> None:
        self.on_changed.fire()

    def _get_value(self) -> _T:
        if self._getter is None:
            raise NotImplementedError

        return self._getter()

    def _set_value(self, new_value: _T) -> None:
        if self._setter is None:
            raise NotImplementedError

        self._setter(new_value)
