from typing import TypeVar, Sequence

from typing_extensions import Protocol

from opendrop.utility.events import Event, EventConnection

TransactionType = TypeVar('TransactionType')


class Source(Protocol[TransactionType]):
    on_new_tx = None  # type: Event

    def _export(self) -> TransactionType:
        """Undocumented"""


class Sink(Protocol[TransactionType]):
    def _apply_tx(self, tx: TransactionType, block: Sequence[EventConnection] = tuple()) -> None:
        """Undocumented"""
