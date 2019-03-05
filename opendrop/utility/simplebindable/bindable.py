import operator
from abc import abstractmethod
from typing import Generic, TypeVar, Callable, Optional

from opendrop.utility.events import Event

_T = TypeVar('_T')


class Bindable(Generic[_T]):
    def __init__(self, check_equals: Callable[[_T, _T], bool] = operator.eq) -> None:
        self.on_changed = Event()

        self._check_equals = check_equals

    def get(self) -> _T:
        return self._get_value()

    def set(self, new_value: _T) -> None:
        current_value = self.get()
        if self._check_equals(current_value, new_value):
            return

        self._set_value(new_value)
        self.on_changed.fire()

    @abstractmethod
    def _get_value(self) -> _T:
        """Actual implementation used to get the value"""

    @abstractmethod
    def _set_value(self, new_value: _T) -> None:
        """Actual implementation used to set a new value"""


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
            raise AttributeError("unreadable bindable")

        return self._getter()

    def _set_value(self, new_value: _T) -> None:
        if self._setter is None:
            raise AttributeError("can't set bindable")

        self._setter(new_value)
