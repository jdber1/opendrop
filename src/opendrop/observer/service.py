from opendrop.observer.bases import Observer, ObserverType
from opendrop.utility.resources import ResourceToken


class ObserverService:
    def get(self, observer_type: ObserverType, **opts) -> Observer:
        return observer_type._provider.provide(**opts)
