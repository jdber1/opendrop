from typing import Callable, Generic, Mapping, Tuple, Type, TypeVar, List

from opendrop.mvp.Model import Model
from opendrop.mvp.handler_metadata import is_handler, handles_what, handles
from opendrop.mvp.IView import IView

T = TypeVar('T', bound=Model)
S = TypeVar('S', bound=IView)


class PresenterMeta(type(Generic)):

    """Metaclass for Presenter, wrapper to hook over `GenericMeta.__getitem__()` magic method to store parametrized type
    information.
    """

    def __getitem__(self, args: Tuple[type, ...]) -> type:
        class ParametrizedPresenter(super().__getitem__(args)):
            _args = args

        return ParametrizedPresenter


class Presenter(Generic[T, S], metaclass=PresenterMeta):
    _args = (object, object)  # type: Tuple[type, ...]

    def __init__(self, model: T, view: S) -> None:
        if not self.can_present(type(view)):
            raise TypeError('{} does not implement {} required by {}'.format(
                type(view).__name__, self.presents_via().__name__, type(self).__name__
            ))

        self.model = model  # type: T
        self.view = view  # type: S

        # Connect the handlers
        self._connect_handlers()

        self.view.connect('on_destroy', self.handle_destroy, immediate=True)

        # Run presenter setup
        self.setup()

    def destroy(self) -> None:
        print('Tearing down', type(self).__name__)
        self.teardown()

    def setup(self) -> None: pass

    def teardown(self) -> None: pass

    # Don't use @handles decorator since currently no support for connect with immediate=True
    # TODO: Allow use of `@handles('on_event', immediate=True)`
    def handle_destroy(self) -> None:
        self.destroy()

    @handles('on_request_close')
    def handle_request_close(self) -> None:
        self.view.close()

    def get_handlers(self) -> Mapping[str, Callable[..., None]]:
        event_handler_map = {}  # Mapping[str, Callable[..., None]]

        for method in (getattr(self, attr_name) for attr_name in dir(self) if callable(getattr(self, attr_name))):
            if is_handler(method):
                event_handler_map[handles_what(method)] = method

        return event_handler_map

    def _connect_handlers(self) -> None:
        event_handler_map = self.get_handlers()  # type: Mapping[str, Callable[..., None]]

        for event_name, handler in event_handler_map.items():
            self.view.connect(event_name, handler)

    @classmethod
    def presents_via(cls) -> Type[IView]:
        return cls._args[1]

    @classmethod
    def can_present(cls, view_cls: Type[IView]) -> bool:
        return issubclass(view_cls, cls.presents_via())
