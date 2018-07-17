from typing import Sequence, Tuple

from opendrop.observer.bases import Observer, ObserverType


class ObserverService:
    def __init__(self, types: Sequence[ObserverType]):
        self._types = tuple(types)

    def new_observer_by_type(self, o_type: ObserverType, **opts) -> Observer:
        assert o_type in self._types
        return o_type._provider.provide(**opts)

    def get_types(self) -> Tuple[ObserverType]:
        return self._types
