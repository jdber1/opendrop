from typing import TypeVar, Callable

from opendrop.utility.events import Event
from . import typing
from .binding import Binding
from .misc import _general_purpose_equality_check

_T = TypeVar('_T')


class Bindable(typing.Bindable[_T]):
    def __init__(self, check_equals: Callable[[_T, _T], bool] = _general_purpose_equality_check) -> None:
        self.on_changed = Event()

        self._check_equals = check_equals

    def get(self) -> _T:
        return self._get_value()

    def set(self, value: _T) -> None:
        try:
            current_value = self.get()
        except NotImplementedError:
            pass
        else:
            if self._check_equals(current_value, value):
                return

        self._set_value(value)

        self.on_changed.fire()

    def bind(self, dst: typing.Bindable[_T]) -> typing.Binding:
        return Binding(src=self, dst=dst)

    def bind_to(self, dst: typing.WriteBindable[_T]) -> typing.Binding:
        return Binding(src=self, dst=dst, one_way=True)

    def bind_from(self, src: typing.ReadBindable[_T]) -> typing.Binding:
        return Binding(src=src, dst=self, one_way=True)

    def _get_value(self) -> _T:
        """Actual implementation used to get the value"""
        raise NotImplementedError

    def _set_value(self, new_value: _T) -> None:
        """Actual implementation used to set a new value"""
        raise NotImplementedError
