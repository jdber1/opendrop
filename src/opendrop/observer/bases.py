import asyncio
import time
from abc import abstractmethod
from numbers import Number
from typing import Any, Iterator, List, Mapping, MutableMapping, Optional, Type, get_type_hints, Sequence

import numpy as np

from opendrop.utility.events import EventSource


class Observer:
    @abstractmethod
    def timelapse(self, timestamps: Sequence[float]) -> List['Observation']:
        pass

    @abstractmethod
    def preview(self) -> 'ObserverPreview':
        pass


class Observation(EventSource):  # make sure to list the events in the class doc
    def __init__(self) -> None:
        EventSource.__init__(self)

        self.timestamp = -1

        self._ready_event = asyncio.Event()

        self._image = None

    @property
    def image(self) -> np.ndarray:
        return self._image

    @property
    def ready(self) -> bool:
        return self._ready_event.is_set()

    def load(self, image: np.ndarray, timestamp: Optional[Number] = None) -> None:
        if self.ready:
            raise ValueError('Observation has already been loaded.')

        self.timestamp = timestamp if timestamp else time.time()

        self._image = image
        self._ready_event.set()

        self.fire('on_ready', image)

    def __iter__(self):
        yield from self._ready_event.wait()
        return self.image

    __await__ = __iter__


class ObserverPreview(EventSource):  # on_update event, list in doc
    def __init__(self, observer: Observer):
        EventSource.__init__(self)

    @abstractmethod
    def close(self): pass


class ObserverProvider:
    @abstractmethod
    def provide(self, **kwargs) -> Observer: pass


class ObserverType:
    def __init__(self, display: str, provider: ObserverProvider) -> None:
        self.display = display  # type: str

        self._provider = provider  # type: ObserverProvider

    @staticmethod
    def _config_opts_from_hints(hints: Mapping[str, Any]) -> Mapping[str, Mapping[str, Any]]:
        opts = {
            keyword: {'display': keyword, 'type': annotation}
            for keyword, annotation in hints.items() if keyword != 'return'
        }

        return opts

    @property
    def config_opts(self) -> Mapping[str, Mapping[str, Any]]:
        opts = None  # type: Mapping[str, Mapping[str, Any]]

        if hasattr(self._provider, 'CONFIG_OPTS'):
            opts = self._provider.CONFIG_OPTS
        else:
            opts = self._config_opts_from_hints(get_type_hints(self._provider.provide))

        return opts
