from abc import abstractmethod
from typing import Any, Generic, TypeVar, Sequence, Optional, Callable

from opendrop.utility.events import Event, EventConnection

TxT = TypeVar('TxT')
VT = TypeVar('VT')


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


# AbstractAtomicBindable

class AtomicBindableTx(Generic[VT]):
    def __init__(self, value: VT):
        self.value = value

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, AtomicBindableTx):
            return False

        return self.value == other.value


class AtomicBindablePropertyAdapter(Generic[VT]):
    def __init__(self, bn_getter: Callable[[Any], 'AbstractAtomicBindable[VT]']):
        self._bn_getter = bn_getter

    def __get__(self, instance, owner) -> VT:
        if instance is None:
            return self

        return self._bn_getter(instance).get()

    def __set__(self, instance, value) -> None:
        self._bn_getter(instance).set(value)


class AbstractAtomicBindable(Generic[VT], Bindable[AtomicBindableTx[VT]]):
    property_adapter = AtomicBindablePropertyAdapter

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.on_changed = Event()

    @staticmethod
    def create_tx(value: VT) -> AtomicBindableTx[VT]:
        """Create and return a new transaction that when applied to another AbstractAtomicBindable `bn`, should set the
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
        """Force this AbstractAtomicBindable (AAB) to fire its `on_new_tx` event with a transaction representing the
        current value of this AAB. Also fires its `on_changed` event with the current value. Usually called when the
        underlying value of this AAB has changed, but this change was not made using AAB.set().
        """
        self._value_changed(self._raw_get(), bcast_tx=True)

    def _value_changed(self, new_value: VT, bcast_tx: bool) -> None:
        self.on_changed.fire(new_value)
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


# AtomicBindable

class AtomicBindable(AbstractAtomicBindable[VT]):
    def __init__(self, initial: VT):
        super().__init__()
        self._value = initial

    def _raw_get(self) -> VT:
        return self._value

    def _raw_set(self, value: VT) -> None:
        self._value = value


# AtomicBindableAdapter

class AtomicBindableAdapter(AbstractAtomicBindable[VT]):
    def __init__(self, getter: Optional[Callable[[], VT]] = None, setter: Optional[Callable[[VT], None]] = None):
        super().__init__()

        # Quick note, poke() should be called whenever the value that is returned by getter is changed.
        self.getter = getter
        self.setter = setter

    def _raw_get(self) -> VT:
        if self.getter is None:
            raise ValueError("Unreadable bindable (no getter)")

        return self.getter()

    def _raw_set(self, value: VT) -> None:
        if self.setter is None:
            raise ValueError("Can't set bindable (no setter)", self, value)

        self.setter(value)
