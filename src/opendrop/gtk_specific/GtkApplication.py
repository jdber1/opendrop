import asyncio
from typing import Type, Mapping, Any

from gi.repository import Gtk
from opendrop.gtk_specific.GtkHookLoopPolicy import GtkHookLoopPolicy

from opendrop.gtk_specific.GtkView import GtkView
from opendrop.mvp.Application import Application


class GtkApplication(Application):

    """Application that uses the Python GTK+ 3 library

    Attributes:
        APPLICATION_ID  Application ID of the app.
        gtk_app         The underlying Gtk.Application object.
    """

    APPLICATION_ID = None  # type: str

    def __init__(self, *args, **kwargs) -> None:
        super().__init__()

        self.gtk_app = Gtk.Application(*args, application_id=self.APPLICATION_ID, **kwargs)  # type: Gtk.Application

        # Connect Gtk.Application events to this instance's handlers
        for args in (
            ( 'startup', self.handle_gtk_app_startup ),
            (    'open', self.handle_gtk_app_open    ),
            ('activate', self.handle_gtk_app_activate),
            ('shutdown', self.handle_gtk_app_shutdown),
        ): self.gtk_app.connect(*args)

    def initialise_view(self, view_cls: Type[GtkView], src_view: Type[GtkView], view_opts: Mapping[str, Any])\
            -> GtkView:
        return view_cls(gtk_app=self.gtk_app, **view_opts)

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

    # Handle Gtk.Application events
    def handle_gtk_app_startup(self, gtk_app: Gtk.Application) -> None:
        print('Starting up app...')

    def handle_gtk_app_open(self, gkt_app: Gtk.Application, *args, **kwargs) -> None:
        pass

    def handle_gtk_app_activate(self, gtk_app: Gtk.Application) -> None:
        print("Activating app...")
        self.main()

    def handle_gtk_app_shutdown(self, gtk_app: Gtk.Application) -> None:
        print('Shutting down app...')