import threading
from typing import Any, Callable, Mapping, Optional, Sequence, TypeVar

from gi.repository import GObject, Gtk

import injector

T = TypeVar('T')
U = TypeVar('U')

CallableT = TypeVar('CallableT', bound=Callable)


class _CurrentInjector(threading.local):
    injector = None


_current_injector = _CurrentInjector()


class Injector(injector.Injector):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.binder.bind(ComponentFactory, to=ComponentFactory(self))

    @staticmethod
    def current() -> Optional['Injector']:
        return _current_injector.injector

    def call_with_injection(
            self,
            func: Callable[..., T],
            self_: Any = None,
            args: Sequence = (),
            kwargs: Mapping[str, Any] = {}
    ) -> T:
        tmp = _current_injector.injector
        _current_injector.injector = self
        try:
            return super().call_with_injection(func, self_, args, kwargs)
        finally:
            _current_injector.injector = tmp


class ComponentFactory:
    def __init__(self, injector: Injector) -> None:
        self._injector = injector

    def create(self, name: str, **properties) -> Gtk.Widget:
        widget_class = GObject.type_from_name(name).pytype
        return self._injector.create_object(widget_class, additional_kwargs=properties)
