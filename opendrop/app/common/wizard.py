from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Sequence

from opendrop.utility.bindable.bindable import AtomicBindable
from opendrop.utility.bindable.binding import Binding
from opendrop.utility.speaker import Moderator


class WizardPageID(Enum):
    def __init__(self, title: str) -> None:
        self.title = title


class WizardPositionView(ABC):
    # The current active key
    bn_active_key = None  # type: AtomicBindable[Optional[WizardPageID]]

    @abstractmethod
    def add_key(self, key: WizardPageID) -> None:
        """Add `key` as one of the possible keys that the user can be active on."""

    @abstractmethod
    def clear(self) -> None:
        """Clear the view of any previously added keys."""


class WizardPositionPresenter:
    def __init__(self, wizard_mod: Moderator, pages: Sequence[WizardPageID], view: WizardPositionView) -> None:
        view.clear()

        for k in pages:
            view.add_key(k)

        self.__data_bindings = [
            Binding(wizard_mod.bn_active_speaker_key, view.bn_active_key)
        ]

    def destroy(self) -> None:
        for db in self.__data_bindings:
            db.unbind()
