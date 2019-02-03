import asyncio
import functools
import types
import warnings
import weakref
from enum import Enum
from typing import Callable, List, Optional, Any, Mapping, Tuple, Iterable, Union, Coroutine, Sequence

from . import exceptions

Handler = Union[Callable, Coroutine]


# todo: Add documentation for EventConnection lifecycle, explanation of CONNECTED, LAST_CALL, DISCONNECTED
# todo: Make threadsafe
# todo: Warn if connecting a lambda function or functools.partial (or others) without weak_ref=False, this is a common
#       mistake. Alternatively make weak_ref=False the default option, however this may lead to silent memory leaks.
class EventConnection:
    class Status(Enum):
        CONNECTED = 1
        LAST_CALL = 2
        DISCONNECTED = 3

    _handler = None  # type: Union[Callable[[], Handler], Handler]
    __invocation_count = 0  # type: int

    # Callback for when the connection disconnects. For internal use.
    _on_disconnected = None  # type: Optional[Callable[]]

    def __init__(self, event: 'Event', handler: Handler, *, loop: Optional[asyncio.AbstractEventLoop] = None,
                 ignore_args: bool = False, weak_ref: bool = True, once: bool = False):
        if asyncio.iscoroutinefunction(handler) and loop is None:
            loop = asyncio.get_event_loop()

        self.status = EventConnection.Status.CONNECTED
        self.event = event
        self._opts = dict(
            loop=loop,
            ignore_args=ignore_args,
            weak_ref=weak_ref,
            once=once
        )  # type: Mapping[str, Any]
        self._tasks = []  # type: List[asyncio.Future]
        self.handler = handler  # type: Handler

    @property
    def handler(self) -> Handler:
        if self._opts['weak_ref']:
            return self._handler()
        else:
            return self._handler

    @handler.setter
    def handler(self, value: Handler) -> None:
        if self._opts['weak_ref']:
            if isinstance(value, types.MethodType):
                wref = weakref.WeakMethod(value)
            else:
                wref = weakref.ref(value)

            self._handler = wref
        else:
            self._handler = value

    def disconnect(self, _force=False) -> None:
        if self.status is EventConnection.Status.DISCONNECTED:
            raise exceptions.NotConnected

        # If current status is CONNECTED, change to LAST_CALL and remove this connection from the list of connected
        # connections in the associated event.
        if self.status is EventConnection.Status.CONNECTED:
            self.status = EventConnection.Status.LAST_CALL
            # Remove self from parent event's connections list since this is no longer connected.
            self.event._remove_connection(self)

        # Status is currently LAST_CALL, if there are still tasks running, then status will stay as LAST_CALL, otherwise
        # if there are no tasks running, status will change to DISCONNECTED.
        if self._tasks:
            # There are still tasks running, if not forcefully disconnecting, then do nothing and return.
            if not _force: return

            # Force cancel all current tasks, each task will call `_task_done()` when cancelled and that method will
            # then automatically attempt to disconnect this connection again later.
            for t in self._tasks:
                t.cancel()
        else:
            self.status = EventConnection.Status.DISCONNECTED
            if self._on_disconnected is not None:
                self._on_disconnected()

    def _invoke_handler(self, args: Iterable, kwargs: Mapping) -> None:
        if self.status is not EventConnection.Status.CONNECTED: return

        if self.handler is None:
            # Handler has been garbage collected, disconnect.
            self.disconnect()
            return

        if self._opts['ignore_args']:
            args, kwargs = (), {}

        loop = self._opts['loop']
        if asyncio.iscoroutinefunction(self.handler):
            loop = loop if loop is not None else asyncio.get_event_loop()
            self._track_task(loop.create_task(self.handler(*args, **kwargs)))
            # Increment the invocation count after the task is tracked, otherwise if `self._opts['once'] is True`,
            # incrementing before tracking the task would disconnect the connection and then it wouldn't allow us to
            # track the task afterwards.
            self._invocation_count += 1
        else:
            self._invocation_count += 1
            if loop is None:
                self.handler(*args, **kwargs)
            else:
                loop.call_soon(functools.partial(self.handler, *args, **kwargs))

    def _track_task(self, task: asyncio.Future) -> None:
        assert self.status is EventConnection.Status.CONNECTED
        task.add_done_callback(self._task_done)
        self._tasks.append(task)

    def _untrack_task(self, task: asyncio.Future) -> None:
        self._tasks.remove(task)

    def _task_done(self, task: asyncio.Future) -> None:
        self._untrack_task(task)

        if self.status is EventConnection.Status.LAST_CALL and not self._tasks:
            self.disconnect(_force=False)

    @property
    def _invocation_count(self) -> int:
        return self.__invocation_count

    @_invocation_count.setter
    def _invocation_count(self, value: int) -> None:
        self.__invocation_count = value

        if self._opts['once'] and self._invocation_count > 0:
            self.disconnect(_force=False)

    # Public read-only property
    @property
    def invocation_count(self) -> int:
        return self._invocation_count


# todo: Add support for typing to Event, e.g. Event[float], callback will receive float.
class Event:

    # todo: Feature idea, Event.on_new_connection event ?
    def __init__(self):
        self.__connections = []  # type: List[EventConnection]

    def connect(self, handler: Handler, **opts) -> EventConnection:
        """
        Connect function `handler` to the event. `handler` is invoked with the same arguments (and keyword arguments) as
        those that were used to fire the event.

        Note: By default, only a weak reference is maintained to the handler, so if you notice a handler isn't being
        invoked as expected, verify that it has not been garbage collected. A common pitfall is connecting a lambda
        that is acting as a closure with no strong references. In this example, `increment_x` will never be invoked by
        the lambda expression handler as the handler has no strong references.

        >>> class MyClass:
        ...     x = 0
        ...     def connect_to_this_event(self, event):
        ...         event.connect(lambda: self.increment_x)
        ...     def increment_x(self):
        ...         self.x += 1

        Specify `weak_ref=False` if you want the event to keep a strong reference to the handler, however this would
        prevent the handler from being garbage collected (unless it is later disconnected), and in this scenario, the
        MyClass instance will never be garbage collected either as the lambda closure will always hold a strong
        reference to it.

        Therefore `weak_ref=False` is often used with `once=True` for one time event handling.

        :param handler: The function to connect to this event.
        :param loop: Undocumented.
        :param once: Whether the function should only connect once, and automatically disconnect after it is invoked.
        :param ignore_args: Whether the function should be called with no arguments when this event is fired.
        :param weak_ref: Whether this event should only keep a weak reference to the handler.

        :return: a new connection object
        """
        new_conn = EventConnection(self, handler, **opts)
        self._add_connection(new_conn)
        return new_conn

    def disconnect_by_func(self, func: Handler) -> None:
        """Disconnect `func` from this event. If `func` is not connected, raises NotConnected.
        :param func: Event handler to disconnect.
        :return: None
        """
        conn = self._find_connection_by_func(func)
        if not conn: raise exceptions.NotConnected
        conn.disconnect()

    def disconnect_all(self) -> None:
        """Disconnect all connections that are connected
        :return: None
        """
        for conn in self._connections:
            conn.disconnect()

    def fire_with_opts(self, args: Sequence[Any] = tuple(), kwargs: Optional[Mapping[str, Any]] = None,
                       block: Sequence[EventConnection] = tuple()):
        # todo: Copy docs from _invoke_handlers
        if kwargs is None: kwargs = {}

        self._invoke_connections(args, kwargs, block=block)

    def fire(self, *args, **kwargs) -> None:
        """Convenience method. Fire the event, handlers will be invoked with any arguments passed.
        :return: None
        """
        self.fire_with_opts(args, kwargs)

    def is_func_connected(self, func: Handler) -> bool:
        if self._find_connection_by_func(func):
            return True
        else:
            return False

    def _add_connection(self, conn: EventConnection) -> None:
        assert conn not in self._connections
        self.__connections.append(conn)

    def _remove_connection(self, conn: EventConnection) -> None:
        assert conn.status is not EventConnection.Status.CONNECTED
        self.__connections.remove(conn)

    def _find_connection_by_func(self, func: Handler) -> Optional[EventConnection]:
        """Return an `EventConnection` object with handler equal (equality is tested using the `==` operator) to `func`,
        if it exists and is connected, else return None.
        :param func: The handler of the associated `EventConnection` object to be found.
        :return: The associated `EventConnection` object if it exists and is connected.
        """
        for conn in self._connections:
            if conn.handler == func:
                return conn
        else:
            return None

    @property
    def _connections(self) -> Tuple[EventConnection, ...]:
        """A copy of of the list of connections connected, since there's been too many accidental iterations through the
        bare list of connections while inadvertently modifying the elements during iteration (either through disconnects
        or new connections). It is therefore recommended to use this property if you require read-only access to the
        list of current connections. There is no guarantee that all connections in the tuple returned will always be
        connected during the tuple's lifetime, as it is after all, only an immutable copy.
        """
        return tuple(self.__connections)

    @property
    def _num_connections(self) -> int:
        """The number of connections this event has that are currently connected."""
        return len(self._connections)

    # Public interface to `_num_connections`
    num_connections = _num_connections

    def _invoke_connections(self, args: Iterable, kwargs: Mapping[str, Any],
                            block: Sequence[EventConnection] = tuple()) -> None:
        for conn in self._connections:
            # Ignore if connection has disconnected, this may have occurred during execution of some handlers.
            if conn.status is not EventConnection.Status.CONNECTED: continue
            if conn in block: continue
            conn._invoke_handler(args, kwargs)

    def wait(self, loop: Optional[asyncio.AbstractEventLoop] = None) -> Any:
        loop = loop if loop is not None else asyncio.get_event_loop()
        f = loop.create_future()  # type: asyncio.Future

        # An implicit handler created to act as the callback to this event so that once fired, it will set its arguments
        # as the result of `f`.
        def handler(*args, **kwargs):
            if kwargs:
                warnings.warn('Keyword arguments not supported by Event.wait(), ignoring keyword arguments.')

            if len(args) == 0:
                args = None
            elif len(args) == 1:
                args = args[0]

            f.set_result(args)
            conn.disconnect()

        conn = self.connect(handler, weak_ref=False)
        conn._on_disconnected = f.cancel

        async def wait_for_f():
            try:
                return await f
            finally:
                if conn.status is EventConnection.Status.CONNECTED:
                    conn.disconnect()

        return wait_for_f()
