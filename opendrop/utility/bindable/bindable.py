from abc import abstractmethod, ABC
from typing import Any, Generic, TypeVar, Sequence, Optional, Callable, Type, MutableSequence, Iterable

from opendrop.utility.events import Event, EventConnection

TxT = TypeVar('TxT')
VT = TypeVar('VT')
T = TypeVar('T')


# Bindable

class Bindable(Generic[TxT]):
    def __init__(self):
        self.on_new_tx = Event()

    def _apply_tx(self, tx: TxT, block: Sequence[EventConnection] = tuple()):
        new_txs = self._raw_apply_tx(tx)
        new_txs = [tx] if new_txs is None else new_txs

        for new_tx in new_txs:
            self._bcast_tx(new_tx, block=block)

    def _bcast_tx(self, tx: TxT, block: Sequence[EventConnection] = tuple()) -> None:
        self.on_new_tx.fire_with_opts(args=(tx,), block=block)

    @abstractmethod
    def _export(self) -> TxT:
        """Return a transaction that can be applied to another Bindable of the same type to restore its state to this
        Bindable's state.
        """
        pass

    @abstractmethod
    def _raw_apply_tx(self, tx: TxT) -> Optional[Sequence[TxT]]:
        """Apply `tx` and return a sequence of transactions that should be broadcasted as a result of the changes made
        during transaction application. Optionally return None to specify that the same `tx` should be broadcasted.
        Return an empty sequence to specify that no transactions should be broadcasted.
        """
        pass


# AtomicBindable

class AtomicBindableTx(Generic[VT]):
    def __init__(self, value: VT):
        self.value = value

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, AtomicBindableTx):
            return False

        return self.value == other.value


class AtomicBindablePropertyAdapter(Generic[T, VT]):
    def __init__(self, bn_getter: Callable[[T], 'AtomicBindable[VT]']):
        self._bn_getter = bn_getter

    def __get__(self, instance: T, owner: Type[T]) -> VT:
        if instance is None:
            return self

        return self._bn_getter(instance).get()

    def __set__(self, instance: T, value: VT) -> None:
        self._bn_getter(instance).set(value)


class AtomicBindable(Generic[VT], Bindable[AtomicBindableTx[VT]]):
    property_adapter = AtomicBindablePropertyAdapter

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.on_changed = Event()  # emits: ()

    @staticmethod
    def create_tx(value: VT) -> AtomicBindableTx[VT]:
        """Create and return a new transaction that when applied to another AtomicBindable `bn`, should set the
        value that `bn` is storing to `value`.
        """
        return AtomicBindableTx(value)

    def get(self) -> VT:
        return self._raw_get()

    def set(self, value: VT) -> None:
        self._set(value, bcast_tx=True)

    def _set(self, value: VT, bcast_tx: bool) -> None:
        self._raw_set(value)
        self._value_changed(value, bcast_tx=bcast_tx)

    def poke(self) -> None:
        """Force this AtomicBindable (AAB) to fire its `on_new_tx` event with a transaction representing the
        current value of this AAB. Also fires its `on_changed` event. Usually called when the underlying value of this
        AAB has changed, but this change was not made using AAB.set().
        """
        self._value_changed(self._raw_get(), bcast_tx=True)

    def _value_changed(self, new_value: VT, bcast_tx: bool) -> None:
        self.on_changed.fire()
        if bcast_tx:
            self._bcast_tx(self.create_tx(new_value))

    # Bindable abstract methods implementation:

    def _export(self) -> AtomicBindableTx[VT]:
        return self.create_tx(self._raw_get())

    def _raw_apply_tx(self, tx: AtomicBindableTx[VT]):
        self._set(tx.value, bcast_tx=False)

    # My abstract methods:

    # Quick note, require that bn._raw_set(some_value) -> bn._raw_get() == some_value.
    @abstractmethod
    def _raw_get(self) -> VT:
        pass

    @abstractmethod
    def _raw_set(self, value: VT) -> None:
        pass


# AtomicBindableVar

class AtomicBindableVar(AtomicBindable[VT]):
    def __init__(self, initial: VT):
        super().__init__()
        self._value = initial

    def _raw_get(self) -> VT:
        return self._value

    def _raw_set(self, value: VT) -> None:
        self._value = value


# AtomicBindableAdapter

class AtomicBindableAdapter(AtomicBindable[VT]):
    def __init__(self, getter: Optional[Callable[[], VT]] = None, setter: Optional[Callable[[VT], None]] = None):
        super().__init__()

        # Quick note, poke() should be called whenever the value that is returned by getter is changed.
        self.getter = getter
        self.setter = setter

    def _raw_get(self) -> VT:
        if self.getter is None:
            raise AttributeError("Unreadable bindable (no getter)")

        return self.getter()

    def _raw_set(self, value: VT) -> None:
        if self.setter is None:
            raise AttributeError("Can't set bindable (no setter)", self, value)

        self.setter(value)


# MutableSequenceBindable
class MutableSequenceBindableTx(ABC):
    @abstractmethod
    def silent_apply(self, target: 'MutableSequenceBindable') -> None:
        """Apply the transaction onto `target` without `target` broadcasting new transactions."""


class MutableSequenceBindableSetItemTx(Generic[VT], MutableSequenceBindableTx):
    def __init__(self, i: int, v: VT) -> None:
        self._i = i
        self._v = v

    def silent_apply(self, target: 'MutableSequenceBindable') -> None:
        target.__setitem__(self._i, self._v, _bcast_tx=False)


class MutableSequenceBindableDelItemTx(Generic[VT], MutableSequenceBindableTx):
    def __init__(self, i: int) -> None:
        self._i = i

    def silent_apply(self, target: 'MutableSequenceBindable') -> None:
        target.__delitem__(self._i, _bcast_tx=False)


class MutableSequenceBindableInsertTx(Generic[VT], MutableSequenceBindableTx):
    def __init__(self, i: int, v: VT) -> None:
        self._i = i
        self._v = v

    def silent_apply(self, target: 'MutableSequenceBindable') -> None:
        target.insert(self._i, self._v, _bcast_tx=False)


class MutableSequenceBindableGroupedTx(Generic[VT], MutableSequenceBindableTx):
    def __init__(self, txs: Iterable[MutableSequenceBindableTx]) -> None:
        self._txs = list(txs)

    def silent_apply(self, target: 'MutableSequenceBindable') -> None:
        for tx in self._txs:
            tx.silent_apply(target)


class MutableSequenceBindable(Bindable[MutableSequenceBindableTx], MutableSequence[VT]):
    def __init__(self) -> None:
        super().__init__()

        self.on_setitem = Event()
        self.on_delitem = Event()
        self.on_insert = Event()

    def __getitem__(self, i: int) -> VT:
        return self._real_getitem(i)

    def __setitem__(self, i: int, v: VT, _bcast_tx: bool = True) -> None:
        self._real_setitem(i, v)
        self.on_setitem.fire(i, v)
        if _bcast_tx:
            self._bcast_tx(self._create_setitem_tx(i, v))

    def __delitem__(self, i: int, _bcast_tx: bool = True) -> None:
        self._real_delitem(i)
        self.on_delitem.fire(i)
        if _bcast_tx:
            self._bcast_tx(self._create_delitem_tx(i))

    def insert(self, i: int, v: VT, _bcast_tx: bool = True) -> None:
        self._real_insert(i, v)
        self.on_insert.fire(i, v)
        if _bcast_tx:
            self._bcast_tx(self._create_insert_tx(i, v))

    def _export(self) -> MutableSequenceBindableTx:
        return MutableSequenceBindableGroupedTx(
            self._create_insert_tx(i, v) for i, v in enumerate(self)
        )

    def _raw_apply_tx(self, tx: MutableSequenceBindableTx) -> None:
        tx.silent_apply(self)

    @staticmethod
    def _create_setitem_tx(i: int, v: VT) -> MutableSequenceBindableTx:
        return MutableSequenceBindableSetItemTx(i, v)

    @staticmethod
    def _create_delitem_tx(i: int) -> MutableSequenceBindableTx:
        return MutableSequenceBindableDelItemTx(i)

    @staticmethod
    def _create_insert_tx(i: int, v: VT) -> MutableSequenceBindableTx:
        return MutableSequenceBindableInsertTx(i, v)

    @abstractmethod
    def _real_setitem(self, i: int, v: VT) -> None:
        """Actual implementation of __setitem__"""

    @abstractmethod
    def _real_getitem(self, i: int) -> VT:
        """Actual implementation of __getitem__"""

    @abstractmethod
    def _real_delitem(self, i: int) -> None:
        """Actual implementation of __delitem__"""

    @abstractmethod
    def _real_insert(self, i: int, v: VT) -> None:
        """Actual implementation of insert"""


class ListBindable(MutableSequenceBindable[VT]):
    def __init__(self, initial: Optional[Iterable[VT]] = None) -> None:
        super().__init__()
        self._list = list(initial) if initial is not None else []

    def _real_getitem(self, i: int) -> VT:
        return self._list[i]

    def _real_setitem(self, i: int, v: VT) -> None:
        self._list[i] = v
        return

    def _real_delitem(self, i: int) -> None:
        del self._list[i]

    def _real_insert(self, i: int, v: VT) -> None:
        self._list.insert(i, v)

    def __len__(self) -> int:
        return len(self._list)

    def __str__(self) -> str:
        return str(self._list)

    def __repr__(self) -> str:
        return '{}({!r})'.format(type(self).__name__, self._list)
