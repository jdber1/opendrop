from unittest.mock import Mock

from opendrop.observer.bases import ObserverProvider, ObserverType
from opendrop.observer.service import ObserverService


class MyObserverProvider(ObserverProvider):
    provide = Mock()


MY_OBSERVER = ObserverType('My Observer', MyObserverProvider)


class TestObserverService:
    def setup(self):
        self.os = ObserverService()

    def test_get(self):
        self.os.get(MY_OBSERVER)

        MyObserverProvider.provide.assert_called_once_with()
