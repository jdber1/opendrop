from typing import Optional

from opendrop import observer
from opendrop.mvp.Model import Model
from opendrop.observer.bases import ObserverPreview, Observer
from opendrop.observer.service import ObserverService


class ObserverViewerModel(Model):
    def __init__(self):
        super().__init__()

        self.observer_service = ObserverService()  # type: ObserverService
        self.observer_types = observer.types  # type: observer.types

        self._current_observer = None  # type: Optional[Observer]

    @property
    def current_observer(self) -> Optional[Observer]:
        return self._current_observer

    @current_observer.setter
    def current_observer(self, value: Optional[Observer]) -> None:
        self._current_observer = value

        self.events.on_current_observer_changed.fire()
