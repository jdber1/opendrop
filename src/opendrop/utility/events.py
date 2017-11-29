import asyncio
from numbers import Number

from typing import Callable, List

import functools


class HandlerContainer:
    def __init__(self, handler: Callable[..., None], immediate: bool = False, once: bool = False,
                 ignore_args: bool = False) -> None:

        self.handler = handler  # type: Callable[..., None]
        self.immediate = immediate  # type: bool
        self.ignore_args = ignore_args  # type: bool
        self.remaining = 1 if once else float('inf')  # type: Number


class Event(object):
    def __init__(self):
        self._handlers = []  # type: List[HandlerContainer]

    def connect(self, handler: Callable[..., None], immediate: bool = False, once: bool = False,
                ignore_args: bool = False) -> None:

        if asyncio.iscoroutinefunction(handler) and immediate:
            raise ValueError('Can\'t connect coroutine function with immediate=True')

        self._handlers.append(HandlerContainer(handler, immediate=immediate, once=once, ignore_args=ignore_args))

    def disconnect(self, handler: Callable[..., None]) -> None:
        for container in self._handlers:
            if container.handler == handler:
                self._handlers.remove(container)
                break
        else:
            raise HandlerNotConnected

    def fire(self, *args, **kwargs) -> None:
        for container in self._handlers:
            handler = container.handler

            if container.ignore_args:
                args = []
                kwargs = {}

            if container.immediate:
                handler(*args, **kwargs)
            elif asyncio.iscoroutinefunction(handler):
                asyncio.get_event_loop().create_task(handler(*args, **kwargs))
            else:
                asyncio.get_event_loop().call_soon(functools.partial(handler, *args, **kwargs))

            container.remaining -= 1

            if container.remaining == 0:
                self.disconnect(handler)

    def fire_ignore_args(self, *args, **kwargs):
        self.fire()


class HandlerNotConnected(Exception):
    pass
