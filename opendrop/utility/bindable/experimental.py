import itertools
from typing import TypeVar, Optional, Sequence, Callable, Mapping, Union, Any

from opendrop.utility.bindable import SetBindable
from .bindable import AtomicBindable, Bindable, BaseAtomicBindable

TxT = TypeVar('TxT')
VT = TypeVar('VT')


class BindableProxy(Bindable[TxT]):
    def __init__(self, target: Bindable[TxT]) -> None:
        super().__init__()
        self._proxy_target_value = target

    @property
    def _proxy_target(self) -> Bindable[TxT]:
        return self._proxy_target_value

    @_proxy_target.setter
    def _proxy_target(self, new_target: Bindable[TxT]) -> None:
        self._proxy_target_value = new_target
        self._bcast_tx(self._export())

    def _export(self) -> TxT:
        return self._proxy_target._export()

    def _raw_apply_tx(self, tx: TxT) -> Optional[Sequence[TxT]]:
        return self._proxy_target._raw_apply_tx(tx)


class IfExpr(BindableProxy[TxT]):
    def __init__(self, cond: AtomicBindable[bool], true: Bindable[TxT], false: Bindable[TxT]) -> None:
        initial_target = true if cond.get() else false
        super().__init__(target=initial_target)

        self._cond = cond
        self._true = true
        self._false = false

        self._cond.on_changed.connect(self._hdl_cond_changed)

    def _hdl_cond_changed(self) -> None:
        new_target = self._true if self._cond.get() else self._false
        self._proxy_target = new_target


if_expr = IfExpr


# AtomicBindableFunction

ArgType = Union[AtomicBindable, SetBindable]


class AtomicFunctionReturnBindable(BaseAtomicBindable[VT]):
    def __init__(self, func: Callable[..., VT], args: Sequence[ArgType], kwargs: Mapping[str, ArgType]) -> None:
        super().__init__()
        self._func = func
        self._args = tuple(args)
        self._kwargs = dict(kwargs)
        self._result = self._calculate_result()

        for x in itertools.chain(self._args, self._kwargs.values()):
            if not isinstance(x, Bindable):
                continue
            x.on_new_tx.connect(self._update_result, ignore_args=True)

    @staticmethod
    def _transform_to_pod(x: ArgType) -> Any:
        if not isinstance(x, Bindable):
            return x
        bindable = x
        if isinstance(bindable, AtomicBindable):
            return bindable.get()
        elif isinstance(bindable, SetBindable):
            return set(bindable)
        else:
            raise ValueError('Unrecognized bindable type')

    def _calculate_result(self) -> VT:
        args_pod = [self._transform_to_pod(x) for x in self._args]
        kwargs_pod = {k: self._transform_to_pod(v) for k, v in self._kwargs}
        return self._func(*args_pod, **kwargs_pod)

    def _update_result(self) -> None:
        self._result = self._calculate_result()
        self.poke()

    def _raw_get(self) -> VT:
        return self._result

    def _raw_set(self, value: Any):
        raise AttributeError("Can't set")


def bindable_function(func: Callable) -> Callable:
    def wrapper(*args, **kwargs):
        return AtomicFunctionReturnBindable(func, args, kwargs)

    return wrapper
