"""Module is used by the internal MVP framework for setting and getting handler metadata. Handler metadata is set by
using the `@handles` decorator to mark a method as an event handler, this decorator is available through the
`opendrop.mvp` module and should not be imported from `handler_metadata`.
"""

from collections import namedtuple

from typing import Any, Callable, NewType, Optional, TypeVar

# Originally imported `Presenter` to use with type hints, but because this causes a circular dependency with no easy
# solution using python's import machinery, we have to use a workaround.

# from opendrop.mvp.Presenter import Presenter

# Type hints workaround, doesn't really provide any type hinting benefits but will at least allow the rest of the code
# to work. If in the future, circular dependencies are resolved, we can remove this.
Presenter = NewType('Presenter', Any)

T = TypeVar('T')

HANDLER_TAG_NAME = '_presenter_handler_tag'

HandlerMetadata = namedtuple('HandlerMetadata', ['event_name', 'immediate'])


def handles(event_name: str, immediate: Optional[bool] = False) -> Callable[[T], T]:
    """Decorator that specifies the method is an event handler for event `event_name`. Methods with this decorator will
    automatically connect to the specified event on initialisation of the presenter.
    :param event_name: The event name that the handler will connect to
    :param immediate: If the handler should connect with immediate=True or not, see events documentation.
    :return: None
    """
    def decorator(method: T) -> T:
        set_(method, event_name, immediate)

        return method

    return decorator


def get(method: Callable) -> HandlerMetadata:
    if not has(method):
        raise TypeError("{} has not been tagged as a handler".format(method))

    return getattr(method, HANDLER_TAG_NAME)


def set_(method: Callable[[T], T], event_name: str, immediate: Optional[bool] = False) -> None:
    setattr(method, HANDLER_TAG_NAME, HandlerMetadata(event_name, immediate))


def has(method: Callable) -> bool:
    if hasattr(method, HANDLER_TAG_NAME):
        return True

    return False
