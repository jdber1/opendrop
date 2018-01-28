import asyncio
import functools
import types
import weakref
from abc import abstractmethod
from collections import defaultdict
from typing import Callable, List, Optional, Any, Mapping

from . import exceptions
from . import markers


class AwaitableCallback(asyncio.Future):
    def __call__(self, *args, **kwargs) -> None:
        self.set_result(args)


class Event:

    """An event class.
    """

    class HandlerContainer:

        """Utility class for storing connect arguments of handlers which affect callback behaviour.
        """

        def __init__(self, handler: Callable[..., None], immediate: bool = False, once: bool = False,
                     ignore_args: bool = False, strong_ref: bool = False) -> None:

            self._handler = None  # type: Optional[Callable[..., None]]
            self._handler_ref = None  # type: Optional[Callable[[], Callable[..., None]]]

            self.immediate = immediate  # type: bool
            self.ignore_args = ignore_args  # type: bool
            self.remaining = 1 if once else float('inf')  # type: float

            if strong_ref:
                self._handler = handler  # type: Callable[..., None]
            else:
                self._handler_ref = weakref.ref(handler) if not isinstance(handler, types.MethodType) else \
                    weakref.WeakMethod(handler)

        @property
        def handler(self) -> Callable[..., None]:
            if self._handler is not None:
                return self._handler
            elif self._handler_ref is not None:
                return self._handler_ref()

    def __init__(self):
        self._handlers = []  # type: List[Event.HandlerContainer]

    def connect(self, handler: Callable[..., None], immediate: bool = False, once: bool = False,
                ignore_args: bool = False, strong_ref: bool = False) -> None:
        """
        Connect function `handler` to the event. `handler` is invoked with the same arguments (and keyword arguments) as
        what the event is fired with.

        Note: By default, only a weak reference is maintained to the handler, so if you notice a handler isn't being
        invoked as expected, verify that it has not yet been garbage collected. A common pitfall is connecting a lambda
        that is acting as a closure with no strong references. In this example, `increment_x` will never be invoked by
        the lambda expression handler as the handler has no strong references.

        >>> class MyClass:
        ... x = 0
        ... def connect_to_this_event(self, event):
        ...     event.connect(lambda: self.increment_x)
        ... def increment_x(self):
        ...     self.x += 1
        ...

        Pass `strong_ref=True` to connect if you want the event to keep a strong reference to the handler, however if
        the handler is never disconnected later, it will also never be garbage collected, and in this scenario, the
        MyClass instance will never be garbage collected either as the lambda closure will always hold a strong
        reference to it.

        Therefore `strong_ref=True` is often used with `once=True` for one time event handling.

        :param handler: The function to connect to the event.
        :param immediate: Whether the function should be called immediately after the event is fired, or queued onto the
        event loop.
        :param once: Whether the function should only connect once, and automatically disconnect after it is called
        once.
        :param ignore_args: Whether the function should be called with no arguments, ignoring the arguments the event
        was fired with.
        :param strong_ref: Whether the event should keep a strong reference to the handler, default False.
        :return: None
        """
        if asyncio.iscoroutinefunction(handler) and immediate:
            raise ValueError('Can\'t connect coroutine function with immediate=True')

        self._handlers.append(Event.HandlerContainer(handler, immediate=immediate, once=once, ignore_args=ignore_args,
                                                     strong_ref=strong_ref))

    def disconnect(self, handler: Callable[..., None]) -> None:
        """Disconnect `handler` from this event.
        :param handler: Event handler to disconnect.
        :return: None
        """
        for container in self._handlers:
            if container.handler == handler:
                self._handlers.remove(container)
                break
        else:
            raise exceptions.HandlerNotConnected

    def inline(self) -> 'AwaitableCallback':  # TODO: kwargs are ignored, mention in docs, automatically once only, also
        # awaitable callback is a future. Also only holds a weak reference to the returned callback, so if a strong
        # reference is not maintained, the callback is never fired, e.g.
        #
        #     event.inline().add_done_callback(fn)
        #
        # In this situation, you should use `connect` with `once=True` instead:
        #
        #     event.connect(fn, once=True)
        #
        cb = AwaitableCallback()

        self.connect(cb, once=True)

        return cb

    def fire(self, *args, **kwargs) -> None:
        """Fire the event, any arguments are passed through to event handlers
        :return: None
        """
        for container in list(self._handlers):
            handler = container.handler
            if handler is None:
                # Handler has been garbage collected
                self._handlers.remove(container)

                continue

            if container.ignore_args:
                args = []
                kwargs = {}

            container.remaining -= 1

            if container.remaining == 0:
                self.disconnect(handler)

            if container.immediate:
                handler(*args, **kwargs)
            elif asyncio.iscoroutinefunction(handler):
                asyncio.get_event_loop().create_task(handler(*args, **kwargs))
            else:
                asyncio.get_event_loop().call_soon(functools.partial(handler, *args, **kwargs))

    def fire_ignore_args(self, *args, **kwargs):
        """Same as `Event.fire()` but any arguments passed are ignored. Useful for when using as a callback for other
        third-party functions where you want to ignore the callback arguments. Similar to connecting the handlers with
        `ignore_args=True` but this allows handlers to be transparent to the fact that arguments are being ignored.
        :return: None
        """
        self.fire()

    def is_connected(self, handler: Callable) -> bool:
        for container in self._handlers:
            if container.handler == handler:
                return True
        else:
            return False

    @property
    def num_connected(self) -> int:
        return len(self._handlers)


class EventSource:

    """Essentially a defaultdict of events. Also has some helper methods for connecting/disconnecting event handlers.

    Usage:
    >>> es = EventSource()
    >>> es.some_event
    <opendrop.utility.events.events.Event object at 0x10074bd30>
    >>> es['some_event']
    <opendrop.utility.events.events.Event object at 0x10074bd30>
    """

    # _forward = ['connect', 'disconnect', 'inline', 'fire', 'fire_ignore_args', 'is_connected']

    def __init__(self):
        self._events_store = defaultdict(Event)  # type: Mapping[str, Event]

    # Forwarded methods
    #
    # def connect(self, name, *args, **kwargs):
    #     return self._events_store[name].connect(*args, **kwargs)
    #
    # def disconnect(self, name, *args, **kwargs):
    #     return self._events_store[name].disconnect(*args, **kwargs)
    #
    # def inline(self, name, *args, **kwargs):
    #     return self._events_store[name].inline(*args, **kwargs)
    #
    # def fire(self, name, *args, **kwargs):
    #     return self._events_store[name].fire(*args, **kwargs)
    #
    # def fire_ignore_args(self, name, *args, **kwargs):
    #     return self._events_store[name].fire_ignore_args(*args, **kwargs)
    #
    # def is_connected(self, name, *args, **kwargs):
    #     return self._events_store[name].is_connected(*args, **kwargs)
    #
    # def num_connected(self, name: str) -> int:
    #     return self._events_store[name].num_connected

    def _get_event(self, name: str) -> Event:
        return self._events_store[name]

    __getitem__ = _get_event
    __getattr__ = _get_event

    def connect_handlers(self, obj: Any, source_name_filter: Optional[str] = None) -> None:
        """Connect the handlers of an object that are found using dir()."""
        for handler in markers.get_handlers_from_obj(obj, source_name_filter):
            hm = markers.get_handler_metadata(handler)

            self._get_event(hm.event_name).connect(handler, immediate=hm.immediate)

    def disconnect_handlers(self, obj: Any, source_name_filter: Optional[str] = None) -> None:
        """Disconnect the handlers of an object that are found using dir().

        If a new handler was added since the last call to `connect_handlers()`, the subsequent `HandlerNotConnected`
        exception that is raised when attempting to disconnect the not yet connected handler is ignored.

        If a handler has been removed from the object before a call to this function, it will not be found and so will
        not be disconnected."""
        for handler in markers.get_handlers_from_obj(obj, source_name_filter):
            hm = markers.get_handler_metadata(handler)

            try:
                self._get_event(hm.event_name).disconnect(handler)
            except exceptions.HandlerNotConnected:
                pass

    def reconnect_handlers(self, obj: Any, source_name_filter: Optional[str] = None) -> None:
        """Call `disconnect_handlers()` then call `connect_handlers()`"""
        self.disconnect_handlers(obj, source_name_filter)
        self.connect_handlers(obj, source_name_filter)


class HasEvents:
    events = ...  # type: EventSource
