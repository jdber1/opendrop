from unittest.mock import Mock

from opendrop.observer.bases import ObserverProvider, ObserverType
from opendrop.observer.service import ObserverService


class MyObserverProvider(ObserverProvider):
    provide = Mock()


MY_OBSERVER = ObserverType('My Observer', MyObserverProvider)


class TestObserverService:
    def setup(self):
        self.observer_service = ObserverService(types=[MY_OBSERVER])

    def test_new_observer_by_type(self):
        self.observer_service.new_observer_by_type(MY_OBSERVER)

        MyObserverProvider.provide.assert_called_once_with()
