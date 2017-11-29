from typing import Callable, Mapping, Optional, Type

from collections import defaultdict

from opendrop.mvp.IView import IView

from opendrop.utility.events import Event


class View(IView):
    def __init__(self) -> None:
        self.events = defaultdict(Event)  # type: Mapping[str, Event]

        self.setup()

    def destroy(self) -> None:
        self.teardown()
        self.fire('on_destroy')

    def setup(self) -> None: pass

    def teardown(self) -> None: pass

    def close(self, next_view: Optional[Type[IView]] = None) -> None:
        self.fire('on_close', self, next_view)

    def spawn(self, new_view: Type[IView], modal: bool = False) -> None:
        self.fire('on_spawn', self, new_view, modal)

    def fire(self, event_name: str, *args, **kwargs) -> None:
        self.events[event_name].fire(*args, **kwargs)

    def fire_ignore_args(self, event_name: str, *args, **kwargs) -> None:
        self.events[event_name].fire_ignore_args(*args, **kwargs)

    def connect(self, event_name: str, handler: Callable[..., None], *args, **kwargs) -> None:
        self.events[event_name].connect(handler, *args, **kwargs)

    def disconnect(self, event_name: str, handler: Callable[..., None]) -> None:
        self.events[event_name].disconnect(handler)
