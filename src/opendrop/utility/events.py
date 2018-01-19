import asyncio
import functools
import types
import weakref
from collections import defaultdict, namedtuple
from numbers import Number
from typing import Callable, List, Optional, Any, Mapping, TypeVar

T = TypeVar('T')


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


class AwaitableCallback(asyncio.Future):
    def __call__(self, *args, **kwargs) -> None:
        self.set_result(args)


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

    def connect_handlers(self, obj: Any, source_name_filter: Optional[str] = None) -> None:
        """Connect the handlers of an object that could be found using dir()"""
        for handler in get_handlers_from_obj(obj, source_name_filter):
            handler_metadata = get_handler_metadata(handler)

            self.connect(handler_metadata.event_name, handler, immediate=handler_metadata.immediate)

    # disconnect_handlers ignores HandlerNotConnected exceptions
    def disconnect_handlers(self, obj: Any, source_name_filter: Optional[str] = None) -> None:
        """Disconnect the handlers of an object that could be found using dir(), if a new handler was added since
        the call to `connect_handlers()`, the subsequent `HandlerNotConnected` exception that is raised when attempting
        to disconnect it is ignored. Also, if a handler has been removed from the object before a call to this function,
        it will not be found and so will not be disconnected."""
        for handler in get_handlers_from_obj(obj, source_name_filter):
            handler_metadata = get_handler_metadata(handler)

            try:
                self.disconnect(handler_metadata.event_name, handler)
            except HandlerNotConnected:
                pass

    def reconnect_handlers(self, obj: Any, source_name_filter: Optional[str] = None) -> None:
        """Call `disconnect_handlers()` then call `connect_handlers()`"""
        self.disconnect_handlers(obj, source_name_filter)
        self.connect_handlers(obj, source_name_filter)


# Handler metadata functions

HANDLER_TAG_NAME = '_handler_tag'

HandlerMetadata = namedtuple('HandlerMetadata', ['source_name', 'event_name', 'immediate'])


def handler(source_name: str, event_name: str, immediate: Optional[bool] = False) -> Callable[[T], T]:
    """Decorator marks the method as an event handler for event `event_name`. Used in conjunction with
    `EventSource.connect_handlers()`.
    :param source_name: The source name of the handler, see `EventSource.connect_handlers()`.
    :param event_name: The event name that the handler will connect to.
    :param immediate: If the handler should connect with immediate=True or not, see events documentation.
    :return: None
    """

    def decorator(method: T) -> T:
        set_handler(method, source_name, event_name, immediate)

        return method

    return decorator


def get_handler_metadata(method: Callable) -> HandlerMetadata:
    if not is_handler(method):
        raise TypeError("{} has not been tagged as a handler".format(method))

    return getattr(method, HANDLER_TAG_NAME)


def set_handler(method: Callable[[T], T], source: str, event_name: str, immediate: Optional[bool] = False) -> None:
    setattr(method, HANDLER_TAG_NAME, HandlerMetadata(source, event_name, immediate))


def is_handler(method: Callable) -> bool:
    if hasattr(method, HANDLER_TAG_NAME):
        return True

    return False


def get_handlers_from_obj(obj: Any, source_name_filter: Optional[str] = None) -> List[Callable[..., None]]:
    """
    Return the event handlers of this presenter.
    :return: A list of event handlers.
    """
    handlers = []  # List[Callable[..., None]]

    for attr_name in dir(obj):
        try:
            attr = getattr(obj, attr_name)

            if not callable(attr):
                continue

            if is_handler(attr):
                handler_metadata = get_handler_metadata(attr)

                if source_name_filter is None or handler_metadata.source_name == source_name_filter:
                    handlers.append(attr)
        except AttributeError:
            pass

    return handlers


# Exceptions

class HandlerNotConnected(Exception):
    pass
