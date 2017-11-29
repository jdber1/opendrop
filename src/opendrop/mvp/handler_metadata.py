from collections import namedtuple

from typing import Any, Callable, NewType, Optional, TypeVar

# Originally imported `Presenter` to use with type hints, but because this causes a circular dependency with no easy
# solution using python's import machinery, we have to use a workaround.

# from opendrop.mvp.Presenter import Presenter

# Type hints workaround, doesn't really provide any type hinting benefits but will at least allow the rest of the code
# to work. If in the future, circular dependencies are resolved, we can remove this.
Presenter = NewType('Presenter', Any)


HANDLER_TAG_NAME = '_presenter_handler_tag'
PRESENTER_TAG_NAME = '_presenter_iview_tag'

T = TypeVar('T')

HandlerMetadata = namedtuple('HandlerMetadata', ['event_name', 'immediate'])


def is_handler(method: Callable) -> bool:
    if hasattr(method, HANDLER_TAG_NAME):
        return True

    return False


def handles(event_name: str, immediate: Optional[bool] = False) -> Callable[[T], T]:
    def decorator(method: T) -> T:
        setattr(method, HANDLER_TAG_NAME, HandlerMetadata(event_name, immediate))

        return method

    return decorator


def get_handler_metadata(method: Callable) -> HandlerMetadata:
    if not is_handler(method):
        raise TypeError("{} has not been tagged as a handler".format(method))

    return getattr(method, HANDLER_TAG_NAME)


def handles_what(method: Callable) -> str:
    return get_handler_metadata(method).event_name
