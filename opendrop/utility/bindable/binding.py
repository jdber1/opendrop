import functools
from typing import TypeVar, Generic, Optional, overload, Union

from .node import Source, Sink

TxT1 = TypeVar('TxT1')
TxT2 = TypeVar('TxT2')


class SourceAndSink(Source[TxT1], Sink[TxT2]):
    pass


class BindingMITM(Generic[TxT1, TxT2]):
    # These methods should not modify `tx`, they should create new transactions since `tx` is reused for all connected
    # handlers to the `on_new_tx` event of a Source.
    def to_dst(self, tx: TxT1) -> TxT2:
        return tx

    def to_src(self, tx: TxT2) -> TxT1:
        return tx


# Quick note, Binding can't resolve "circular" bindings, e.g.:
#   A - B
#    \ /
#     C
class Binding(Generic[TxT1, TxT2]):
    def __init__(self, src: SourceAndSink[TxT1, TxT2], dst: SourceAndSink[TxT2, TxT1],
                 mitm: Optional[BindingMITM[TxT1, TxT2]] = None):
        self._src = src
        self._dst = dst
        self._mitm = mitm

        self._on_new_tx_conns = {
            id(bn): bn.on_new_tx.connect(functools.partial(self._hdl_new_tx, bn), weak_ref=False)
            for bn in (src, dst)}

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

    @overload
    def _hdl_new_tx(self, from_: Source[TxT1], tx: TxT1) -> None: ...
    @overload
    def _hdl_new_tx(self, from_: Source[TxT2], tx: TxT2) -> None: ...

    def _hdl_new_tx(self, from_, tx) -> None:
        target = self._get_other(from_)

        # Block the event connection connected to `target_bn.on_new_tx` as we don't want to be notified about the change
        # we are about to apply to `target_bn`, otherwise we end up in an infinite feedback loop.
        block_conn = self._on_new_tx_conns[id(target)]

        tx = self._transform_tx(tx, target)

        target._apply_tx(tx, block=(block_conn,))

    @overload
    def _get_other(self, this: Union[Source[TxT1], Sink[TxT2]]) -> SourceAndSink[TxT2, TxT1]: ...
    @overload
    def _get_other(self, this: Union[Source[TxT2], Sink[TxT1]]) -> SourceAndSink[TxT1, TxT2]: ...

    def _get_other(self, this):
        """Return the `src` bindable if `bn` is `dst`, else return the `dst` bindable."""
        assert this in (self._src, self._dst)

        if this is self._src:
            return self._dst
        else:
            return self._src

    @overload
    def _transform_tx(self, tx: TxT1, target: Sink[TxT2]) -> TxT2: ...
    @overload
    def _transform_tx(self, tx: TxT2, target: Sink[TxT1]) -> TxT1: ...

    def _transform_tx(self, tx, target):
        assert target in (self._src, self._dst)

        if self._mitm is None:
            return tx

        if target is self._dst:
            return self._mitm.to_dst(tx)
        else:
            return self._mitm.to_src(tx)
