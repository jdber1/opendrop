from typing import Optional, Type, Any, Mapping, TypeVar

from opendrop.mvp.IView import IView
from opendrop.mvp.Model import Model
from opendrop.utility.events import Event
from opendrop.utility.strategy import strategy

T = TypeVar('T', bound=IView)


class View(IView):

    """The view class, responsible for presenting the user interface to the user and notifying the presenter of user
    inputs.
    """

    PREVIOUS = 0  # type: int

    class _Events:
        def __init__(self):
            self.on_setup_done = Event()
            self.on_request_close = Event()
            self.on_destroy = Event()

    def __init__(self) -> None:
        """View constructor.
        """
        self.events = self._Events()

        self._hidden = False  # type: bool

        self._destroyed = False  # type: bool

    def destroy(self) -> None:
        """Destroy the view (called by the Application object, use `close()` to end the View from the Presenter
        instead). This method will call `teardown()` and fire the 'on_destroy' event afterwards.
        :return: None
        """
        self._destroyed = True

        self.teardown()
        self.events.on_destroy.fire()

    def do_setup(self) -> None:
        """Wrapper for `setup` so after setup is complete, 'on_setup_done' event is fired. Called by `Application` after
        `__init__` is completed.
        :return: None
        """
        self.setup()
        self.events.on_setup_done.fire()

    def setup(self) -> None:
        """Override to perform setup tasks such as creating and displaying widgets.
        :return: None
        """
        pass

    def teardown(self) -> Any:
        """Called after `destroy()`, override to perform any clean up tasks such as releasing resources.
        """
        pass

    @strategy
    def close(self) -> None:
        """Destroy the view.

        The `Application` will provide an implementation to this strategy to destroy the view when called.
        :return: None
        """
        pass

    @strategy
    def spawn(self, view_cls: Type[T], model: Model = None, child: bool = False,
              view_opts: Optional[Mapping[str, Any]] = None) -> T:
        """Spawn a new view.

        The `Application` will provide an implementation to this strategy to spawn a new view when called.

        If the new view is spawned as a child of this view, then when `close()` is called on this view, all child views
        will be closed first before closing this view.

        :param view_cls: The class of the view to spawn.
        :param model: The model object that should be given to the presenter.
        :param child: If the spawned view should be a child of this view.
        :param view_opts: Keyword arguments to be passed to the constructor of the to be spawned view.
        :return:
        """
        pass

    # Properties

    @property
    def hidden(self) -> bool:
        """Return True if the current view is hidden and False if it's not.
        :return: Hidden state.
        """
        return self._hidden

    @hidden.setter
    def hidden(self, value: bool):
        self._hidden = value

    @property
    def destroyed(self) -> bool:
        return self._destroyed
