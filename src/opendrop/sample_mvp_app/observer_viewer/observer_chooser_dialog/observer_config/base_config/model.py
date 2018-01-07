from abc import abstractmethod
from typing import MutableMapping, Any

from opendrop.mvp.Model import Model


class ObserverConfigRequest(Model):
    @property
    @abstractmethod
    def opts(self) -> MutableMapping[str, Any]: pass