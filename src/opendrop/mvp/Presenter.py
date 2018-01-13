from typing import Callable, Generic, List, Mapping, Tuple, Type, TypeVar, NewType, Any, Union, Optional

from opendrop.mvp import handles

from opendrop.mvp import handler_metadata

from opendrop.mvp.Model import Model
from opendrop.mvp.IView import IView
from opendrop.utility.events import EventSource

T = TypeVar('T', bound=Model)
S = TypeVar('S', bound=IView)


class PresenterMeta(type(Generic)):

    """Metaclass for Presenter, wrapper to hook over `GenericMeta.__getitem__()` magic method to store parametrized type
    information.
    """

    def __getitem__(self, args: Tuple[Optional[Type[Model]], Type[IView]]) -> type:
        class ParametrizedPresenter(super().__getitem__(args)):
            _args = args

        return ParametrizedPresenter


class Presenter(Generic[T, S], EventSource, metaclass=PresenterMeta):
    IGNORE = False  # type: bool

    _args = (Model, IView)  # type: Tuple[Optional[Type[Model]], Type[IView]]

    def __init__(self, model: Optional[T], view: S) -> None:
        """
        :param model: The model object used by the presenter.
        :param view: The view to be presented by the presenter.
        """
        if not self.can_control(type(view)):
            raise TypeError('{} does not implement {} required by {}'.format(
                type(view).__name__, self.controls_via().__name__, type(self).__name__
            ))

        EventSource.__init__(self)

        self.model = model  # type: Optional[T]

        self.view = view  # type: S

        self._connect_handlers()

    def do_setup(self) -> None:
        """Wrapper for `setup` to be consistent with `View.do_setup()`. Called by `Application` after presenter is
        initialised (and context is created). `Application` will always call this after the presenter's view has been
        initialised
        :return: None
        """
        self.setup()

    def setup(self) -> None:
        """Setup the presenter, override for any setup work that needs to be done.
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

        for attr_name in dir(self):
            try:
                attr = getattr(self, attr_name)

                if not callable(attr):
                    continue

                if handler_metadata.has_metadata(attr):
                    handlers.append(attr)
            except AttributeError:
                pass

        return handlers

    @classmethod
    def controls_via(cls) -> Type[IView]:
        """Return the view interface that the presenter uses.
        :return: The view interface.
        """
        return cls._args[1]

    @classmethod
    def can_control(cls, iview: Type[IView]) -> bool:
        """Check if this presenter is able to present the given view class.
        :param iview: IView class object in question.
        :return: True if presenter can present, False otherwise.
        """
        return issubclass(iview, cls.controls_via())

    # Private methods

    def destroy(self) -> None:
        """Destroy the presenter object. Called automatically by `Application` after the associated view has been
        destroyed, should not be called directly.
        :return: None
        """
        print('Tearing down', type(self).__name__)  # DEBUG
        self.teardown()

    def _connect_handlers(self) -> None:
        handlers = self.get_handlers()  # type: List[Callable[..., None]]

        request_close_handled = False  # type: bool

        for handler in handlers:
            metadata = handler_metadata.get(handler)  # type: handler_metadata.HandlerMetadata

            if metadata.source_name == 'view':
                self.view.connect(metadata.event_name, handler, immediate=metadata.immediate)

                if metadata.event_name == 'on_request_close':
                    request_close_handled = True

            elif metadata.source_name == 'model':
                self.model.connect(metadata.event_name, handler, immediate=metadata.immediate)

        if not request_close_handled:
            self.view.connect('on_request_close', self._handle_request_close)

    # Event handlers

    def _handle_request_close(self) -> None:
        self.view.close()
