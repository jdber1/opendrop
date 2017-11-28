from typing import Any, Callable, TypeVar, NewType, Mapping

# Originally imported `Presenter` to use with type hints, but because this causes a circular dependency with no easy
# solution using python's import machinery, we have to use a workaround.

# from opendrop.mvp.Presenter import Presenter

# Type hints workaround, doesn't really provide any type hinting benefits but will at least allow the rest of the code
# to work. If in the future, circular dependencies are resolved, we can remove this.
Presenter = NewType('Presenter', Any)


HANDLER_TAG_NAME = '_presenter_handler_tag'
PRESENTER_TAG_NAME = '_presenter_iview_tag'

T = TypeVar('T')


def is_handler(method: Callable) -> bool:
    if hasattr(method, HANDLER_TAG_NAME):
        return True

    return False


def handles(event_name: str) -> Callable[[T], T]:
    def decorator(method: T) -> T:
        setattr(method, HANDLER_TAG_NAME, event_name)

        return method

    return decorator


def handles_what(method: Callable) -> str:
    if not is_handler(method):
        raise TypeError("{} has not been tagged as a handler".format(method))

    return getattr(method, HANDLER_TAG_NAME)
