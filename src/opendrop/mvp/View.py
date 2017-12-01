from typing import Mapping, Optional, Type

from collections import defaultdict

from opendrop.mvp.IView import IView

from opendrop.utility.events import Event


class View(IView):

    """The view class, responsible for presenting the user interface to the user and notifying the presenter of user
    inputs.
    """

    def __init__(self) -> None:
        """View constructor, this will call `setup()` after initialisation has finished.
        """
        self.events = defaultdict(Event)  # type: Mapping[str, Event]

        self.setup()

    def destroy(self) -> None:
        """Destroy the view (called by the Application object, use `close()` to end the View from the Presenter
        instead). This method will call `teardown()` and fire the 'on_destroy' event afterwards.
        :return: None
        """
        self.teardown()
        self.fire('on_destroy')

    def setup(self) -> None:
        """Called after initialisation of this View, override to perform setup tasks such as creating and
        displaying widgets.
        """
        pass

    def teardown(self) -> None:
        """Called after `destroy()`, override to perform any clean up tasks such as releasing resources.
        """
        pass

    def close(self, next_view: Optional[Type[IView]] = None) -> None:
        """Called by the presenter to end the view. This method will fire the 'on_close' event which the Application
        is connected to. If an optional `next_view` argument is specified, the Application will destroy this view and
        setup `next_view` and its presenter. If `next_view` is not specified, the Application will just destroy the
        view.
        :param next_view: Next view to show.
        :return: None
        """
        self.fire('on_close', self, next_view)

    def spawn(self, new_view: Type[IView], modal: bool = False) -> None:
        """Spawn a new view alongside this view.

        TODO: currently not implemented by Application

        :param new_view: New view to spawn
        :param modal: If the new view is modal to this view
        :return: None
        """
        self.fire('on_spawn', self, new_view, modal)

    def fire(self, event_name: str, *args, **kwargs) -> None:
        """Convenience method for calling `fire()` on the `event_name` event. All other arguments are passed through to
        `Event.fire()`.
        See documentation for `Event.fire()`
        :param event_name: Name of the event to fire
        :return: None
        """
        self.events[event_name].fire(*args, **kwargs)

    def fire_ignore_args(self, event_name: str, *args, **kwargs) -> None:
        """Convenience method for calling `fire_ignore_args()` on the `event_name` event. All other arguments are passed
        through to `Event.fire_ignore_args()`.
        See documentation for `Event.fire_ignore_args()`
        :param event_name: Name of the event to fire
        :return: None
        """
        self.events[event_name].fire_ignore_args(*args, **kwargs)

    def connect(self, event_name: str, *args, **kwargs) -> None:
        """Convenience method for calling `connect()` on the `event_name` event. All other arguments are passed
        through to `Event.connect()`.
        See documentation for `Event.connect()`
        :param event_name: Name of the event to connect to
        :return: None
        """
        self.events[event_name].connect(*args, **kwargs)

    def disconnect(self, event_name: str, *args, **kwargs) -> None:
        """Convenience method for calling `disconnect()` on the `event_name` event. All other arguments are passed
        through to `Event.disconnect()`.
        See documentation for `Event.disconnect()`
        :param event_name: Name of the event to disconnect from
        :return: None
        """
        self.events[event_name].disconnect(*args, **kwargs)
