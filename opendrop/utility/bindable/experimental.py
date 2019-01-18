from typing import TypeVar, Optional, Sequence

from .bindable import AtomicBindable, Bindable


TxT = TypeVar('TxT')


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
