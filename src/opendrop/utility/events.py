import asyncio
import functools
import types
import weakref
from collections import defaultdict
from numbers import Number
from typing import Callable, List, Optional, Tuple, Any, Mapping


class EventSource:

    """Essentially an events container, has all the same methods as `Event` but instead the first parameter takes the
    event name of the event to perform the action on.

    Usage:

        class MyClass(EventSource):
            def __init__(self):
                EventSource.__init__(self)
                # class initialisation

        def handle_my_event(arg):
            print(arg)

        obj = MyClass()

        obj.connect('on_my_event', handle_my_event)
        obj.fire('on_my_event', 'Hello')  # fires `handle_my_event()` with arg='Hello'
    """

    _forward = ['connect', 'disconnect', 'inline', 'fire', 'fire_ignore_args', 'is_connected']

    def __init__(self):
        self._events_store = defaultdict(Event)  # type: Mapping[str, Event]

    def __getattribute__(self, name: str) -> Any:
        if name.startswith('_') or name not in self._forward:
            return super().__getattribute__(name)

        def f(event_name: str, *args, **kwargs):
            return getattr(self._events_store[event_name], name)(*args, **kwargs)

        return f

    def num_connected(self, name: str) -> int:
        return self._events_store[name].num_connected


class Event:

    """An event class.
    """

    def __init__(self):
        self._handlers = []  # type: List[HandlerContainer]

    def connect(self, handler: Callable[..., None], immediate: bool = False, once: bool = False,
                ignore_args: bool = False, strong_ref: bool = False) -> None:
        """
        Connect function `handler` to the event. `handler` is invoked with the same arguments (and keyword arguments) as
        what the event is fired with.
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

        self._handlers.append(HandlerContainer(handler, immediate=immediate, once=once,
                                               ignore_args=ignore_args, strong_ref=strong_ref))

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
            raise HandlerNotConnected

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

class AwaitableCallback(asyncio.Future):
    def __call__(self, *args, **kwargs):
        self.set_result(args)


class HandlerContainer:

    """Utility class for storing connect arguments of handlers which affect callback behaviour.
    """

    def __init__(self, handler: Callable[..., None], immediate: bool = False, once: bool = False,
                 ignore_args: bool = False, strong_ref: bool = False) -> None:

        self._handler = None  # type: Optional[Callable[..., None]]
        self._handler_ref = None  # type: Optional[Callable[[], Callable[..., None]]]

        self.immediate = immediate  # type: bool
        self.ignore_args = ignore_args  # type: bool
        self.remaining = 1 if once else float('inf')  # type: Number

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


class EventSourceProxy:
    class EventSourceListenToContainer:
        def __init__(self, event_source: EventSource, descriptor_args: Optional[Tuple[Any, Any]] = None) -> None:
            self.event_source = event_source  # type: EventSource
            self.descriptor_args = descriptor_args  # type: Optional[Tuple[Any, Any]]

    def __init__(self) -> None:
        self._clean_events_store = {}  # type: MutableMapping[str, Event]
        self._dirty_events_store = {}
        self._sources = []  # type: List[EventSourceProxy.EventSourceListenToContainer]

    def listen_to(self, event_source: EventSource) -> None:

        self._sources.append(EventSourceProxy.EventSourceListenToContainer(event_source, ))

    def connect(self, name: str, *args, **kwargs):
        def wrapper(handler):
            self._get_proxy_event(name).connect(handler, *args, **kwargs)

        return wrapper

    def _new_proxy_event(self, name: str) -> Event:
        assert name not in self._events_store

        new_event = Event()

        self._events_store[name] = new_event

        for event_source in self._sources:
            event_source.hi

    def _get_proxy_event(self, name: str) -> Event:
        if name not in self._events_store:
            self._new_proxy_event(name)

        return self._events_store[name]

class HandlerNotConnected(Exception):
    pass
