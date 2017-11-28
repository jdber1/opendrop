import asyncio

from typing import Callable

import functools


class Event(object):
    def __init__(self):
        self._handlers = []

    def connect(self, handler: Callable[..., None]) -> None:
        self._handlers.append(handler)

    def disconnect(self, handler: Callable[..., None]) -> None:
        try:
            self._handlers.remove(handler)
        except ValueError:
            raise HandlerNotConnected

    def fire(self, *args, **kwargs):
        for handler in self._handlers:
            if asyncio.iscoroutinefunction(handler):
                asyncio.get_event_loop().create_task(handler(*args, **kwargs))
            else:
                asyncio.get_event_loop().call_soon(functools.partial(handler, *args, **kwargs))


class HandlerNotConnected(Exception):
    pass
