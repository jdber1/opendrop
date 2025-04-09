from typing import TypeVar, Callable, Optional

from . import abc

_T = TypeVar('_T')


class VariableBindable(abc.Bindable[_T]):
    def __init__(self, initial: _T, **kwargs) -> None:
        super().__init__(**kwargs)

        self._value = initial

    def _get_value(self) -> _T:
        return self._value

    def _set_value(self, new_value: _T) -> None:
        self._value = new_value


class AccessorBindable(abc.Bindable[_T]):
    def __init__(
            self,
            getter: Optional[Callable[[], _T]] = None,
            setter: Optional[Callable[[_T], None]] = None,
            **kwargs
    ) -> None:
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
