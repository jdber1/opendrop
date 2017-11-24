from typing import Callable, TypeVar, Mapping

# TODO: what is a class type typehint?

from opendrop.app.presenters import BasePresenter
from opendrop.utility.events import Event


HANDLER_TAG_NAME = '_presenter_handler_tag'

        # # TODO: how to typehint for loops
        # for event_name in event_name_handler_map:
        #     setattr(controllable, event_name, EventProperty(event_name))

# T = TypeVar('T', Callable)
def handles(event_name: str):  # -> Callable[[T], T]:
    def decorator(method):  # T) -> T:
        setattr(method, HANDLER_TAG_NAME, event_name)

        return method

    return decorator


def is_handler(method: Callable) -> bool:
    if hasattr(method, HANDLER_TAG_NAME):
        return True

    return False


def which_handler(method: Callable) -> str:
    if not is_handler(method):
        raise TypeError("{} has not been tagged as a handler".format(method))

    return getattr(method, HANDLER_TAG_NAME)


def get_handlers(presenter_cls: BasePresenter) -> Mapping[str, Callable]:
    event_name_handler_map = {}

    for k, v in presenter_cls.__dict__.items():
        if is_handler(v):
            event_name = which_handler(v)  # type: str

            event_name_handler_map[event_name] = v


    return event_name_handler_map
