from typing import Callable, Generic, List, Mapping, Tuple, Type, TypeVar

from opendrop.mvp.handler_metadata import is_handler, handles, get_handler_metadata

from opendrop.mvp.Model import Model
from opendrop.mvp.IView import IView

T = TypeVar('T', bound=Model)
S = TypeVar('S', bound=IView)


class PresenterMeta(type(Generic)):

    """Metaclass for Presenter, wrapper to hook over `GenericMeta.__getitem__()` magic method to store parametrized type
    information.
    """

    def __getitem__(self, args: Tuple[Type[Model], Type[IView]]) -> type:
        class ParametrizedPresenter(super().__getitem__(args)):
            _args = args

        return ParametrizedPresenter


class Presenter(Generic[T, S], metaclass=PresenterMeta):
    _args = (Model, IView)  # type: Tuple[Type[Model], Type[IView]]

    def __init__(self, model: T, view: S) -> None:
        """
        :param model: The model object used by the presenter.
        :param view: The view to be presented by the presenter.
        """
        if not self.can_present(type(view)):
            raise TypeError('{} does not implement {} required by {}'.format(
                type(view).__name__, self.presents_via().__name__, type(self).__name__
            ))

        self.model = model  # type: T
        self.view = view  # type: S

        self._connect_handlers()

        self.setup()

    def setup(self) -> None:
        """Called after presenter is initialised. Application will always initialise the presenter's view first before
        the presenter so this method is always called after view has been set up. Override for any setup work that needs
        to be done.
        :return: None
        """
        pass

    def teardown(self) -> None:
        """Called when the presenter is being destroyed (which is after the view has been destroyed). Override to
        clean-up setup work such as releasing resources.
        :return: None
        """
        pass

    def get_handlers(self) -> List[Callable[..., None]]:
        """
        Return the event handlers of this presenter.
        :return: A list of event handlers.
        """
        handlers = []  # List[Callable[..., None]]

        for method in (getattr(self, attr_name) for attr_name in dir(self) if callable(getattr(self, attr_name))):
            if is_handler(method):
                handlers.append(method)

        return handlers

    @classmethod
    def presents_via(cls) -> Type[IView]:
        """Return the view interface that the presenter uses.
        :return: The view interface.
        """
        return cls._args[1]

    @classmethod
    def can_present(cls, view_cls: Type[IView]) -> bool:
        """Check if this presenter is able to present the given view class.
        :param view_cls: View class object in question.
        :return: True if presenter can present, False otherwise.
        """
        return issubclass(view_cls, cls.presents_via())

    # Private methods

    def _destroy(self) -> None:
        """Destroy the presenter object. Called automatically after the associated view has been destroyed.
        :return: None
        """
        print('Tearing down', type(self).__name__)  # DEBUG
        self.teardown()

    def _connect_handlers(self) -> None:
        handlers = self.get_handlers()  # List[Callable[..., None]]

        for handler in handlers:
            metadata = get_handler_metadata(handler)

            self.view.connect(metadata.event_name, handler, immediate=metadata.immediate)

    # Event handlers

    @handles('on_destroy', immediate=True)
    def _handle_destroy(self) -> None:
        self._destroy()

    @handles('on_request_close')
    def _handle_request_close(self) -> None:
        self.view.close()
