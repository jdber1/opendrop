from typing import Generic, Tuple, Type, TypeVar, Optional

from opendrop.mvp.Model import Model
from opendrop.mvp.View import View
from opendrop.utility.events import EventSource, handler

T = TypeVar('T', bound=Model)
S = TypeVar('S', bound=View)


class PresenterMeta(type(Generic)):

    """Metaclass for Presenter, wrapper to hook over `GenericMeta.__getitem__()` magic method to store parametrized type
    information.
    """

    def __getitem__(self, args: Tuple[Optional[Type[Model]], Type[View]]) -> type:
        class ParametrizedPresenter(super().__getitem__(args)):
            _args = args

        return ParametrizedPresenter


class Presenter(Generic[T, S], EventSource, metaclass=PresenterMeta):
    IGNORE = False  # type: bool

    _args = (Model, View)  # type: Tuple[Optional[Type[Model]], Type[View]]

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

    @classmethod
    def controls_via(cls) -> Type[View]:
        """Return the view interface that the presenter uses.
        :return: The view interface.
        """
        return cls._args[1]

    @classmethod
    def can_control(cls, view: Type[View]) -> bool:
        """Check if this presenter is able to present the given view class.
        :param view: View class object in question.
        :return: True if presenter can present, False otherwise.
        """
        return issubclass(view, cls.controls_via())

    # Private methods

    def destroy(self) -> None:
        """Destroy the presenter object. Called automatically by `Application` after the associated view has been
        destroyed, should not be called directly.
        :return: None
        """
        print('Tearing down', type(self).__name__)  # DEBUG
        self.teardown()

    def _connect_handlers(self) -> None:
        self.view.connect_handlers(self, 'view')
        self.model.connect_handlers(self, 'model')

    # Event handlers

    @handler('view', 'on_request_close')
    def _handle_request_close(self) -> None:
        if self.view.num_connected('on_request_close') == 1 \
           and self.view.is_connected('on_request_close', self._handle_request_close):
            self.view.close()
