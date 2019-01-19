from typing import TypeVar, Generic, Optional, Callable

from .bindable import AtomicBindableTx, BaseAtomicBindable
from .binding import BindingMITM

SVT = TypeVar('SVT')
DVT = TypeVar('DVT')


class AtomicBindingMITM(Generic[SVT, DVT], BindingMITM[AtomicBindableTx[SVT], AtomicBindableTx[DVT]]):
    def __init__(self, to_dst: Optional[Callable[[SVT], DVT]] = None, to_src: Optional[Callable[[DVT], SVT]] = None):
        if to_dst is not None:
            self._atomic_to_dst = to_dst

        if to_src is not None:
            self._atomic_to_src = to_src

    def to_dst(self, tx: AtomicBindableTx[SVT]) -> AtomicBindableTx[DVT]:
        new_tx = BaseAtomicBindable._create_tx(self._atomic_to_dst(tx.value))
        return new_tx

    def to_src(self, tx: AtomicBindableTx[DVT]) -> AtomicBindableTx[SVT]:
        new_tx = BaseAtomicBindable._create_tx(self._atomic_to_src(tx.value))
        return new_tx

    def _atomic_to_dst(self, value: SVT) -> DVT:
        return value

    def _atomic_to_src(self, value: DVT) -> SVT:
        return value
