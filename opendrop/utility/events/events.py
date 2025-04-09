# Copyright © 2020, Joseph Berry, Rico Tabor (opendrop.dev@gmail.com)
# OpenDrop is released under the GNU GPL License. You are free to
# modify and distribute the code, but always under the same license
#
# If you use this software in your research, please cite the following
# journal articles:
#
# J. D. Berry, M. J. Neeson, R. R. Dagastine, D. Y. C. Chan and
# R. F. Tabor, Measurement of surface and interfacial tension using
# pendant drop tensiometry. Journal of Colloid and Interface Science 454
# (2015) 226–237. https://doi.org/10.1016/j.jcis.2015.05.012
#
# E. Huang, T. Denning, A. Skoufis, J. Qi, R. R. Dagastine, R. F. Tabor
# and J. D. Berry, OpenDrop: Open-source software for pendant drop
# tensiometry & contact angle measurements, submitted to the Journal of
# Open Source Software
#
# These citations help us not only to understand who is using and
# developing OpenDrop, and for what purpose, but also to justify
# continued development of this code and other open source resources.
#
# OpenDrop is distributed WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.  You
# should have received a copy of the GNU General Public License along
# with this software.  If not, see <https://www.gnu.org/licenses/>.


import asyncio
import types
import warnings
import weakref
from enum import Enum
from typing import Callable, List, Optional, Any, Mapping, Tuple, Iterable, Union, Sequence

from . import exceptions


class EventConnection:
    class Status(Enum):
        CONNECTED = 0
        DISCONNECTED = 1

    _handler = None  # type: Optional[Union[Callable[[], Callable], Callable]]
    __invocation_count = 0

    # Callback for when the connection disconnects. For internal use.
    _on_disconnected = None  # type: Optional[Callable[[], Any]]

    def __init__(self, event: 'Event', handler: Callable, *,
                 ignore_args: bool = False, weak_ref: bool = True, once: bool = False):
        self.status = EventConnection.Status.CONNECTED
        self.event = event
        self._opts = dict(
            ignore_args=ignore_args,
            weak_ref=weak_ref,
            once=once
        )
        self.handler = handler

    @property
    def handler(self) -> Callable:
        if self._opts['weak_ref']:
            return self._handler()
        else:
            return self._handler

    @handler.setter
    def handler(self, value: Callable) -> None:
        if self._opts['weak_ref']:
            if isinstance(value, types.MethodType):
                wref = weakref.WeakMethod(value)
            else:
                wref = weakref.ref(value)

            self._handler = wref
        else:
            self._handler = value

    def disconnect(self) -> None:
        if self.status is EventConnection.Status.DISCONNECTED:
            raise exceptions.NotConnected

        self.status = EventConnection.Status.DISCONNECTED

        # Remove self from parent event's connections list
        self.event._remove_connection(self)

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

        self._invocation_count += 1
        self.handler(*args, **kwargs)

    @property
    def _invocation_count(self) -> int:
        return self.__invocation_count

    @_invocation_count.setter
    def _invocation_count(self, value: int) -> None:
        self.__invocation_count = value

        if self._opts['once'] and self._invocation_count > 0:
            self.disconnect()

    # Public read-only property
    @property
    def invocation_count(self) -> int:
        return self._invocation_count


class Event:
    def __init__(self):
        self.__connections = []  # type: List[EventConnection]

    def connect(self, handler: Callable, **opts) -> EventConnection:
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
        prevent the handler from being garbage collected (unless it is later disconnected, or the event itself is
        garbage collected), and in this scenario, the MyClass instance will never be garbage collected either as the
        lambda closure holds a reference to it.

        Therefore `weak_ref=False` is often used with `once=True` for one time event handling.

        :param handler:
            The function to connect to this event.
        :param once:
            Whether the function should only connect once, and automatically disconnect after it is invoked.
        :param ignore_args:
            Whether the function should be called with no arguments when this event is fired.
        :param weak_ref:
            Whether this event should only keep a weak reference to the handler.

        :return:
            A new `EventConnection` object.
        """
        new_conn = EventConnection(self, handler, **opts)
        self._add_connection(new_conn)
        return new_conn

    def disconnect_by_func(self, func: Callable) -> None:
        """Disconnect `func` from this event. If `func` is not connected, raises NotConnected.

        :param func:
            The function to disconnect.
        :return:
            None
        """
        conn = self._find_connection_by_func(func)
        if not conn: raise exceptions.NotConnected
        conn.disconnect()

    def disconnect_all(self) -> None:
        """Disconnect all connected handlers.

        :return:
            None
        """
        for conn in self._connections:
            conn.disconnect()

    def fire_with_opts(self, args: Sequence[Any] = tuple(), kwargs: Optional[Mapping[str, Any]] = None,
                       block: Sequence[EventConnection] = tuple()):
        """Fire the event, handlers will be invoked with arguments `args` and keyword-arguments `kwargs`. Handlers
        can be selectively blocked by specifying their `EventConnection`s in the `block` parameter."""
        if kwargs is None: kwargs = {}
        self._invoke_connections(args, kwargs, block=block)

    def fire(self, *args, **kwargs) -> None:
        """Fire the event, handlers will be invoked with any arguments passed.

        :return:
            None
        """
        self.fire_with_opts(args, kwargs)

    def is_func_connected(self, func: Callable) -> bool:
        """Return True if `func` is connected."""
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

    def _find_connection_by_func(self, func: Callable) -> Optional[EventConnection]:
        """Return an `EventConnection` object with handler equal (equality is tested using the `==` operator) to
        `func`, if it exists and is connected, else return None.

        :param func:
            The handler of the associated `EventConnection` object to be found.
        :return:
            The associated `EventConnection` object if it exists, else None.
        """
        for conn in self._connections:
            if conn.handler == func:
                return conn
        else:
            return None

    @property
    def _connections(self) -> Tuple[EventConnection, ...]:
        """A copy of of the list of connections connected, since there's been too many accidental iterations through
        the raw list of connections while inadvertently modifying the elements during iteration (either through
        disconnects or new connections). It is therefore recommended to use this property if you require read-only
        access to the list of current connections. There is no guarantee that all connections in the tuple returned
        will always be connected during the tuple's lifetime, as it is after all only an immutable copy.
        """
        return tuple(self.__connections)

    @property
    def num_connections(self) -> int:
        """The number of connections this event has."""
        return len(self._connections)

    def _invoke_connections(self, args: Iterable, kwargs: Mapping[str, Any],
                            block: Sequence[EventConnection] = tuple()) -> None:
        for conn in self._connections:
            # Ignore if connection has disconnected, this may have occurred during execution of some handlers.
            if conn.status is not EventConnection.Status.CONNECTED: continue
            if conn in block: continue
            conn._invoke_handler(args, kwargs)

    def wait(self, loop: Optional[asyncio.AbstractEventLoop] = None) -> Any:
        """Create a `Future` object belonging on `loop` and connect a callback to this event such that when the
        event fires, the `Future` object's result is set with the arguments the event was fired with.
        Keyword-arguments are ignored. Return an awaitable that awaits to the result of the `Future` object.
        """
        loop = loop if loop is not None else asyncio.get_event_loop()
        f = loop.create_future()  # type: asyncio.Future

        # An implicit handler created to act as the callback to this event so that once fired, it will set its
        # arguments it was invoked with as the result of `f`.
        def handler(*args, **kwargs):
            if f.cancelled():
                # Future was cancelled 'just before' event was fired, ignore.
                return

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
