import functools
from typing import TypeVar, Generic, Optional, Callable

from opendrop.utility.bindable.bindable import Bindable, AtomicBindableTx, AbstractAtomicBindable

TxT = TypeVar('TxT')
VT = TypeVar('VT')


# Binding

class BindingMITM(Generic[TxT]):
    # These methods should not modify `tx`, they should create new transactions since `tx` is reused for all connected
    # handlers to the `on_new_tx` event of a Bindable.
    def to_dst(self, tx: TxT) -> TxT:
        return tx

    def to_src(self, tx: TxT) -> TxT:
        return tx


# Quick note, Binding can't resolve "circular" bindings, e.g.:
#   A - B
#    \ /
#     C
class Binding(Generic[TxT]):
    def __init__(self, src: Bindable[TxT], dst: Bindable[TxT], mitm: Optional[BindingMITM[TxT]] = None):
        self._src = src
        self._dst = dst
        self._mitm = mitm

        self._on_new_tx_conns = {
            bn: bn.on_new_tx.connect(functools.partial(self._hdl_new_tx, bn), immediate=True, strong_ref=True)
            for bn in (src, dst)
        }

        # Export the state of `src` to `dst`.
        self._hdl_new_tx(src, src._export())

    def unbind(self) -> None:
        """Unbind the bound bindables, new transactions in one will no longer be applied to the other. This Binding will
        will also no longer hold a reference to the bounded bindables.
        """
        for conn in self._on_new_tx_conns.values():
            conn.disconnect()

        del self._src
        del self._dst

        # Delete the connections as well since they also hold a reference to `_src` and `_dst` (through the
        # functools.partial object).
        del self._on_new_tx_conns

    def _hdl_new_tx(self, bn: Bindable[TxT], tx: TxT) -> None:
        target = self._get_other(bn)

        # Block the event connection connected to `target_bn.on_new_tx` as we don't want to be notified about the change
        # we are about to apply to `target_bn`, otherwise we end up in an infinite feedback loop.
        block_conn = self._on_new_tx_conns[target]

        tx = self._transform_tx(tx, target)

        target._apply_tx(tx, block=(block_conn,))

    def _get_other(self, this: Bindable[TxT]) -> Bindable[TxT]:
        """Return the `src` bindable if `bn` is `dst`, else return the `dst` bindable."""
        assert this in (self._src, self._dst)

        if this is self._src:
            return self._dst
        else:
            return self._src

    def _transform_tx(self, tx: TxT, target: Bindable[TxT]) -> TxT:
        assert target in (self._src, self._dst)

        if self._mitm is None:
            return tx

        if target is self._dst:
            return self._mitm.to_dst(tx)
        else:
            return self._mitm.to_src(tx)


# AtomicBindingMITM

class AtomicBindingMITM(Generic[VT], BindingMITM[AtomicBindableTx[VT]]):
    def __init__(self, to_dst: Optional[Callable[[VT], VT]] = None, to_src: Optional[Callable[[VT], VT]] = None):
        if to_dst is not None:
            self._atomic_to_dst = to_dst

        if to_src is not None:
            self._atomic_to_src = to_src

    def to_dst(self, tx: AtomicBindableTx[VT]):
        new_tx = AbstractAtomicBindable.create_tx(self._atomic_to_dst(tx.value))
        return new_tx

    def to_src(self, tx: AtomicBindableTx[VT]):
        new_tx = AbstractAtomicBindable.create_tx(self._atomic_to_src(tx.value))
        return new_tx

    def _atomic_to_dst(self, value: VT) -> VT:
        return value

    def _atomic_to_src(self, value: VT) -> VT:
        return value
