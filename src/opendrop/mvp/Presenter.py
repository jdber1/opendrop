from abc import ABC, abstractmethod
from typing import Any, Callable, Generic, Mapping, TypeVar

from opendrop.mvp.handler_metadata import is_handler, handles_what, handles
from opendrop.mvp.IView import IView

T = TypeVar('T')
S = TypeVar('S', bound=IView)


class PresenterMeta(type(Generic)):

    """Metaclass for Presenter, wrapper to hook over `GenericMeta__getitem__()` magic method to store parametrized type
    """

    def __getitem__(self, args):
        class ParametrizedPresenter(super().__getitem__(args)):
            _args = args

        return ParametrizedPresenter


class Presenter(ABC, Generic[T, S], metaclass=PresenterMeta):
    _args = [object, object]

    def __init__(self, model: T, view: S) -> None:
        if not self.can_present(type(view)):
            raise TypeError('{} does not implement {} required by {}'.format(
                type(view).__name__, self.presents_via().__name__, type(self).__name__
            ))

        self.model = model  # type: T
        self.view = view  # type: S

        self._connect_handlers()

        self.setup()

    def destroy(self) -> None:
        self.teardown()

    def setup(self) -> None: pass

    def teardown(self) -> None: pass

    @handles('on_destroy')
    def handle_destroy(self) -> None:
        self.destroy()

    @handles('on_request_close')
    def handle_request_close(self):
        self.view.close()

    def get_handlers(self) -> Mapping[str, Callable[..., None]]:
        event_handler_map = {}

        for method in (getattr(self, attr_name) for attr_name in dir(self) if callable(getattr(self, attr_name))):
            if is_handler(method):
                event_handler_map[handles_what(method)] = method

        return event_handler_map

    def _connect_handlers(self) -> None:
        event_handler_map = self.get_handlers()  # type: Mapping[str, Callable[..., None]]

        for event_name, handler in event_handler_map.items():
            self.view.connect(event_name, handler)

    @classmethod
    def presents_via(cls) -> type:
        return cls._args[1]

    @classmethod
    def can_present(cls, view_cls: type) -> bool:
        return issubclass(view_cls, cls.presents_via())