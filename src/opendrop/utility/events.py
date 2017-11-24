import asyncio

from typing import Callable

import functools

class Event(object):
    def __init__(self):
        self._listeners = []

    def connect(self, listener: Callable) -> None:
        self._listeners.append(listener)

    def disconnect(self, listener: Callable) -> None:
        try:
            self._listeners.remove(listener)
        except ValueError:
            raise ListenerNotConnected

    def fire(self, *args, **kwargs):
        for listener in self._listeners:
            asyncio.get_event_loop().call_soon(functools.partial(listener, *args, **kwargs))


class ListenerNotConnected(Exception):
    pass
