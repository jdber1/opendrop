import itertools
from typing import Callable, TypeVar

from . import abc, typing

_T = TypeVar('_T')


class _FunctionApplierBindable(abc.Bindable[_T]):
    def __init__(
            self,
            function: Callable[..., _T],
            *bn_args: typing.ReadBindable,
            **bn_kwargs: typing.ReadBindable
    ) -> None:
        super().__init__()

        self._function = function
        self._bn_args = bn_args
        self._bn_kwargs = bn_kwargs

        for bn_arg in itertools.chain(bn_args, bn_kwargs.values()):
            bn_arg.on_changed.connect(self._arguments_changed)

    def _arguments_changed(self):
        self.on_changed.fire()

    def _get_value(self) -> _T:
        args = [bn.get() for bn in self._bn_args]
        kwargs = {key: bn.get() for key, bn in self._bn_kwargs.items()}

        return self._function(*args, **kwargs)

    def _set_value(self, new_value: _T) -> None:
        raise NotImplementedError("can't set bindable result of apply()")


apply = _FunctionApplierBindable
