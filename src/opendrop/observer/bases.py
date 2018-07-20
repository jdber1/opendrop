import asyncio
import time
from abc import abstractmethod
from asyncio import Future
from numbers import Number
from typing import Any, List, Mapping, Optional, get_type_hints, Sequence

import numpy as np

from opendrop.utility.events import Event


class Observer:
    _o_type = None  # type: Optional[ObserverType]

    @abstractmethod
    def timelapse(self, timestamps: Sequence[float]) -> List['Observation']:
        pass

    @abstractmethod
    def preview(self) -> 'ObserverPreview':
        pass

    def _register_type(self, o_type: 'ObserverType') -> None:
        assert self._o_type is None
        self._o_type = o_type

    @property
    def type(self) -> 'ObserverType':
        return self._o_type


class Observation:
    def __init__(self, volatile: bool = False) -> None:
        self.on_ready = Event()  # emits: (image: np.ndarray)

        self.timestamp = None
        self.volatile = volatile

        self._image = None
        self._ready_event = asyncio.Event()
        self._waiters = []  # type: List[asyncio.Future]
        self._cancelled = False

    def load(self, image: np.ndarray, timestamp: Optional[Number] = None) -> None:
        if self.ready:
            raise ValueError('Observation is already loaded.')

        self.timestamp = timestamp if timestamp is not None else time.time()

        self._image = image

        self._sweep_waiters()

        self.on_ready.fire(image)

    def cancel(self) -> None:
        if self.cancelled:
            return

        self._cancelled = True

        for fut in self._waiters:
            fut.set_exception(ObservationCancelled)

    @property
    def cancelled(self) -> bool:
        return self._cancelled

    @property
    def image(self) -> np.ndarray:
        return self._image

    @property
    def time_until_ready(self) -> float:
        return 0.0

    @property
    def ready(self) -> bool:
        if self.cancelled:
            return False

        return self.image is not None

    def _add_waiter(self, fut: Future) -> None:
        if not self._update_waiter(fut):
            self._waiters.append(fut)

    def _update_waiter(self, fut: Future) -> bool:
        if self.cancelled:
            fut.set_exception(ObservationCancelled)
            return True

        if self.ready:
            fut.set_result(self.image)
            return True

        return False

    def _sweep_waiters(self) -> None:
        for fut in self._waiters:
            if self._update_waiter(fut):
                self._waiters.remove(fut)

    def __iter__(self):
        fut = asyncio.get_event_loop().create_future()  # type: Future
        self._add_waiter(fut)

        return fut.__await__()

    __await__ = __iter__


class ObserverPreview:
    def __init__(self, observer: Observer):
        self.on_changed = Event()  # emits: (preview_image: np.ndarray)

    @abstractmethod
    def close(self): pass

    @property
    @abstractmethod
    def buffer(self) -> np.ndarray:
        """Pixel array (should be rgb) of the current preview"""


class ObserverProvider:
    @abstractmethod
    def provide(self, **kwargs) -> Observer: pass


class ObserverType:
    def __init__(self, name: str, provider: ObserverProvider) -> None:
        self.name = name  # type: str

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


# Exceptions
class ObservationCancelled(Exception):
    pass
