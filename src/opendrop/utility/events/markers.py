from collections import namedtuple
from typing import Callable, TypeVar, Optional, Any, List

T = TypeVar('T')

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
