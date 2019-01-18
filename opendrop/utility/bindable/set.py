import functools
from abc import ABC, abstractmethod
from collections import Set, MutableSet
from typing import TypeVar, Generic, Iterable, Iterator, Union, MutableSequence, Any

from opendrop.utility.bindable.bindable import Bindable
from opendrop.utility.events import Event

VT = TypeVar('VT')


class SetBindableTx(ABC):
    @abstractmethod
    def silent_apply(self, target: 'ModifiableSetBindable') -> None:
        """Apply the transaction onto `target` without `target` broadcasting new transactions."""


class SetBindableAddItemTx(Generic[VT], SetBindableTx):
    def __init__(self, x: VT) -> None:
        self._x = x

    def silent_apply(self, target: 'ModifiableSetBindable') -> None:
        if self._x in target:
            return
        target.add(self._x, _bcast_tx=False)


class SetBindableDiscardItemTx(Generic[VT], SetBindableTx):
    def __init__(self, x: VT) -> None:
        self._x = x

    def silent_apply(self, target: 'ModifiableSetBindable') -> None:
        if self._x not in target:
            return
        target.discard(self._x, _bcast_tx=False)


class SetBindableGroupedTx(Generic[VT], SetBindableTx):
    def __init__(self, txs: Iterable[SetBindableTx]) -> None:
        self._txs = list(txs)

    def silent_apply(self, target: 'ModifiableSetBindable') -> None:
        for tx in self._txs:
            tx.silent_apply(target)


class SetBindable(Generic[VT], Bindable[SetBindableTx], Set):
    def __init__(self) -> None:
        super().__init__()
        self.on_add = Event()
        self.on_discard = Event()

    def union(self, *others: Union[Iterable[VT], 'SetBindable[VT]']) -> 'SetBindable[VT]':
        return SetUnionBindable(self, *others)

    def _add(self, x: VT, _bcast_tx: bool = True) -> None:
        self._actual_add(x)
        self.on_add.fire(x)
        if _bcast_tx:
            self._bcast_tx(SetBindableAddItemTx(x))

    def _discard(self, x: VT, _bcast_tx: bool = True) -> None:
        self._actual_discard(x)
        self.on_discard.fire(x)
        if _bcast_tx:
            self._bcast_tx(SetBindableDiscardItemTx(x))

    @abstractmethod
    def _actual_add(self, x: VT) -> None:
        """Actual implementation of add()"""

    @abstractmethod
    def _actual_discard(self, x: VT) -> None:
        """Actual implementation of discard"""

    def _export(self) -> SetBindableTx:
        return SetBindableGroupedTx(
            SetBindableAddItemTx(x)
            for x in self)

    def _raw_apply_tx(self, tx: Any) -> None:
        raise ValueError('This set bindable is read-only.')


class SetUnionBindable(SetBindable[VT]):
    def __init__(self, *sources: SetBindable[VT]) -> None:
        super().__init__()
        self._result = set()  # type: MutableSequence(Set[VT])
        self._sources = []  # type: MutableSequence(SetBindable[VT])
        self._handler_refs = []  # type: MutableSequence

        for source in sources:
            self._result |= set(source)

            hdl_add = functools.partial(self._hdl_set_add, source)
            self._handler_refs.append(hdl_add)
            hdl_discard = functools.partial(self._hdl_set_discard, source)
            self._handler_refs.append(hdl_discard)

            source.on_add.connect(hdl_add)
            source.on_discard.connect(hdl_discard)

            self._sources.append(source)

    def _hdl_set_add(self, src: SetBindable[VT], x: VT) -> None:
        if x in self._result:
            return
        self._add(x)

    def _hdl_set_discard(self, src: SetBindable[VT], x: VT) -> None:
        contains_elsewhere = False
        for elsewhere in self._sources:
            if elsewhere is src:
                continue
            if x in elsewhere:
                contains_elsewhere = True

        if contains_elsewhere:
            return

        self._discard(x)

    def _actual_add(self, x: VT) -> None:
        self._result.add(x)

    def _actual_discard(self, x: VT) -> None:
        self._result.discard(x)

    def __contains__(self, x: VT) -> bool:
        return x in self._result

    def __len__(self) -> int:
        return len(self._result)

    def __iter__(self) -> Iterator[VT]:
        return iter(self._result)


class ModifiableSetBindable(SetBindable[VT], MutableSet):
    def add(self, x: VT, _bcast_tx: bool = True) -> None:
        self._add(x, _bcast_tx)

    def discard(self, x: VT, _bcast_tx: bool = True) -> None:
        self._discard(x, _bcast_tx)

    def _raw_apply_tx(self, tx: SetBindableTx) -> None:
        tx.silent_apply(self)


# SetBindable that uses the builtin set as the underlying implementation.
class BuiltinSetBindable(ModifiableSetBindable[VT]):
    def __init__(self, initial_value: Iterable[VT]) -> None:
        super().__init__()
        self._set = set(initial_value)

    def _actual_add(self, x: VT) -> None:
        self._set.add(x)

    def _actual_discard(self, x: VT) -> None:
        self._set.discard(x)

    def __contains__(self, x: VT) -> bool:
        return x in self._set

    def __len__(self) -> int:
        return len(self._set)

    def __iter__(self) -> Iterator[VT]:
        return iter(self._set)
