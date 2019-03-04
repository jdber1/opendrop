import itertools
from typing import TypeVar, Optional, Sequence, Callable, Mapping, Any, overload

from .bindable import AtomicBindable, Bindable, AtomicBindableVar

BindableType = TypeVar('BindableType', bound=Bindable)
TxT1 = TypeVar('TxT1')
TxT2 = TypeVar('TxT2')


class BindableProxy(Bindable[TxT1, TxT2]):
    def __init__(self, target: Bindable[TxT1, TxT2]) -> None:
        super().__init__()
        self._proxy_target_value = None  # type: Optional[Bindable[TxT1, TxT2]]
        self._proxy_target_cleanup_tasks = []
        self._proxy_target = target

    def __call__(self, bindable: BindableType) -> BindableType:
        self.bind_to(bindable)
        return bindable

    @property
    def _proxy_target(self) -> Bindable[TxT1, TxT2]:
        return self._proxy_target_value

    @_proxy_target.setter
    def _proxy_target(self, new_target: Bindable[TxT1, TxT2]) -> None:
        self._remove_current_proxy_target()
        self._proxy_target_value = new_target
        self._proxy_target_cleanup_tasks.append(
            new_target.on_new_tx.connect(self._bcast_tx).disconnect)
        self._bcast_tx(self._export())

    def _remove_current_proxy_target(self) -> None:
        for f in self._proxy_target_cleanup_tasks:
            f()
        self._proxy_target_cleanup_tasks = []
        self._proxy_target_value = None

    def _export(self) -> TxT2:
        return self._proxy_target._export()

    def _raw_apply_tx(self, tx: TxT1) -> Optional[Sequence[TxT2]]:
        return self._proxy_target._raw_apply_tx(tx)


class IfExpr(BindableProxy[TxT1, TxT2]):
    def __init__(self, cond: AtomicBindable[bool], true: Bindable[TxT1, TxT2], false: Bindable[TxT1, TxT2]) -> None:
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


class FunctionApplierBindable(BindableProxy[TxT1, TxT2]):
    def __init__(self, func: Callable, args: Sequence[AtomicBindable], kwargs: Mapping[str, AtomicBindable]) -> None:
        self._func = func
        self._args = tuple(args)
        self._kwargs = dict(kwargs)
        initial_result = self._calculate_result()

        super().__init__(self._convert_to_bindable(initial_result))

        for x in itertools.chain(self._args, self._kwargs.values()):
            if not isinstance(x, Bindable):
                continue
            x.on_new_tx.connect(self._update, ignore_args=True)

    @staticmethod
    def _convert_to_pod(x: AtomicBindable) -> Any:
        if not isinstance(x, Bindable):
            return x
        bindable = x
        if isinstance(bindable, AtomicBindable):
            return bindable.get()
        else:
            raise ValueError('Unrecognized bindable type')

    @staticmethod
    def _convert_to_bindable(x: Any) -> AtomicBindable:
        return AtomicBindableVar(x)

    def _calculate_result(self) -> Any:
        args_pod = [self._convert_to_pod(x) for x in self._args]
        kwargs_pod = {k: self._convert_to_pod(v) for k, v in self._kwargs.items()}
        return self._func(*args_pod, **kwargs_pod)

    def _update(self) -> None:
        result = self._calculate_result()
        self._proxy_target = self._convert_to_bindable(result)

    def _raw_apply_tx(self, tx: Any) -> None:
        raise ValueError("Can't apply transactions to this.")


class FunctionBindableWrapper:
    def __init__(self, func: Callable, autobind_return: Optional[Callable[[], Bindable]] = None) -> None:
        self._func = func
        self._autobind_return = autobind_return

    def __call__(self, *args, **kwargs) -> Any:
        result = FunctionApplierBindable(self._func, args, kwargs)
        if self._autobind_return:
            result = result(self._autobind_return())
        return result


@overload
def bindable_function(*, autobind_return: Optional[Callable[[], Bindable]] = None) -> Callable: ...
@overload
def bindable_function(func: Callable) -> Callable: ...
@overload
def bindable_function(func: Callable, autobind_return: Optional[Callable[[], Bindable]] = None) -> Callable: ...

def bindable_function(func=None, **kwargs):
    if func is None:
        def inner(func: Callable) -> Callable:
            return bindable_function(func, **kwargs)
        return inner

    return FunctionBindableWrapper(func, **kwargs)
