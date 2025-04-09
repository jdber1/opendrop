from abc import abstractmethod
from typing import Generic, TypeVar

from opendrop.utility.events import Event

_T = TypeVar('_T')


class ReadBindable(Generic[_T]):
    on_changed = None  # type: Event

    @abstractmethod
    def get(self) -> _T:
        """Return the value of this."""

    @abstractmethod
    def bind_to(self, dst: 'WriteBindable[_T]') -> 'Binding':
        """Create a one-way binding from this to dst and return the Binding object."""


class WriteBindable(Generic[_T]):
    @abstractmethod
    def set(self, value: _T) -> None:
        """Set the value of this."""

    @abstractmethod
    def bind_from(self, src: ReadBindable[_T]) -> 'Binding':
        """Create a one-way binding from src to this and return the Binding object."""


class Bindable(ReadBindable[_T], WriteBindable[_T]):
    @abstractmethod
    def bind(self, dst: 'Bindable[_T]') -> 'Binding':
        """Create a two-way binding from this to dst and return the Binding object."""


class Binding:
    def unbind(self) -> None:
        """Unbind the bound Bindables, new changes in one will no longer be applied to the other. This object will also
        no longer hold a reference to the bounded Bindables.
        """
