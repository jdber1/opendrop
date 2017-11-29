import asyncio
from typing import Callable, Type, Mapping, List, Optional

from gi.repository import Gtk

from opendrop.sample_app.GtkHookLoopPolicy import GtkHookLoopPolicy
from opendrop.sample_app.presenters.BurgerExamplePresenter import BurgerExamplePresenter
from opendrop.sample_app.presenters.MainPresenter import MainPresenter
from opendrop.sample_app.presenters.TimerExamplePresenter import TimerExamplePresenter
from opendrop.sample_app.views.MainView import MainView
from opendrop.sample_app.views.TimerExampleView import TimerExampleView

from opendrop.mvp.Model import Model
from opendrop.mvp.Presenter import Presenter
from opendrop.mvp.View import View
from opendrop.mvp.ViewPresenterMap import ViewPresenterMap
from opendrop.sample_app.views.BurgerExampleView import BurgerExampleView
from opendrop.utility.events import Event


class Application:
    APPLICATION_ID = 'org.example.sampleapp'  # type: str

    ENTRY_VIEW = MainView  # type: Type[View]

    VIEWS = [MainView, TimerExampleView, BurgerExampleView]  # type: List[View]
    PRESENTERS = [MainPresenter, TimerExamplePresenter, BurgerExamplePresenter]  # type: List[Presenter]

    _VPMAP = ViewPresenterMap(views=VIEWS, presenters=PRESENTERS)  # type: ViewPresenterMap
    assert ENTRY_VIEW in VIEWS

    def __init__(self, *args, **kwargs) -> None:
        self.gtk_app = Gtk.Application(*args, application_id=self.APPLICATION_ID, **kwargs)  # type: Gtk.Application

        # Connect Gtk.Application events to this instance's handlers
        for args in (
            ( 'startup', self.handle_gtk_app_startup ),
            (    'open', self.handle_gtk_app_open    ),
            ('activate', self.handle_gtk_app_activate),
            ('shutdown', self.handle_gtk_app_shutdown),
        ): self.gtk_app.connect(*args)

        self.active_views = []  # type: List[View]

        # Currently empty, events might be added in the future possibly
        self.events = []  # type: List[str]

        self.events = {event_name: Event() for event_name in self.events}  # type: Mapping[str, Event]

    def add_active_view(self, view: View) -> None:
        self.active_views.append(view)

    def remove_active_view(self, view: View) -> None:
        self.active_views.remove(view)

        if not self.active_views:
            self.quit()

    def new_view(self, view_cls: Type[View]) -> None:
        model = None  # type: Optional[Model]
        view = view_cls(gtk_app=self.gtk_app)  # type: View

        presenter_cls = self.presenter_from_view(view_cls)  # type: Type[Presenter]

        # Create and wire up the presenter
        presenter_cls(model, view)

        # Connect view events
        view.connect('on_close', self.handle_view_close)

        self.add_active_view(view)

    def handle_view_close(self, src_view: View, next_view_cls: Type[View]) -> None:
        if next_view_cls:
            self.new_view(next_view_cls)

        self.remove_active_view(src_view)
        src_view.destroy()

    def presenter_from_view(self, view_cls: Type[View]) -> Type[Presenter]:
        return self._VPMAP.presenter_from_view(view_cls)

    def run(self, *args, **kwargs) -> None:
        asyncio.set_event_loop_policy(GtkHookLoopPolicy())
        asyncio.set_event_loop(asyncio.new_event_loop())
        asyncio.get_event_loop().run_forever()

        self.gtk_app.run(*args, **kwargs)

    def quit(self) -> None:
        # Stop the event loop and reset the event loop policy to the default policy
        asyncio.get_event_loop().stop()
        asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
        asyncio.set_event_loop(asyncio.new_event_loop())

        # Quit the Gtk.Application object
        self.gtk_app.quit()

    def fire(self, event_name: str, *args, **kwargs) -> None:
        self.events[event_name].fire(*args, **kwargs)

    def connect(self, event_name: str, handler: Callable[..., None], *args, **kwargs) -> None:
        self.events[event_name].connect(handler, *args, **kwargs)

    def disconnect(self, event_name: str, handler: Callable[..., None]) -> None:
        self.events[event_name].disconnect(handler)

    # Handle Gtk.Application events
    def handle_gtk_app_startup(self, gtk_app: Gtk.Application) -> None:
        print('Starting up app...')

    def handle_gtk_app_open(self, gkt_app: Gtk.Application, *args, **kwargs) -> None:
        pass

    def handle_gtk_app_activate(self, gtk_app: Gtk.Application) -> None:
        print("Activating app...")
        self.new_view(self.ENTRY_VIEW)

    def handle_gtk_app_shutdown(self, gtk_app: Gtk.Application) -> None:
        print('Shutting down app...')