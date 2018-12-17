import asyncio
from typing import MutableSequence, Callable

from gi.repository import Gtk, Gdk

from opendrop.app.app import AppGUI, AppGUIFactory
from opendrop.app.header import HeaderView, HeaderPresenter
from opendrop.component.stack import StackModel, StackView, StackPresenter
from opendrop.utility.speaker import Moderator


class DefaultAppGUI(AppGUI):
    def __init__(self, main_mod: Moderator, content_stack: StackModel):
        # Private attributes
        self._loop = asyncio.get_event_loop()
        self._main_mod = main_mod
        self._content_stack = content_stack
        self._window = Gtk.Window()
        self._destroy_funcs = []  # type: MutableSequence[Callable[[],None]]

        # Add widgets to the window.
        self._populate_window()

        self._destroy_funcs.append(self._window.destroy)
        self._window.connect('delete-event', self._hdl_window_delete_event)
        self._window.show_all()

    def _populate_window(self) -> None:
        body = Gtk.Grid()
        self._window.add(body)

        content_view = StackView()
        body.attach(content_view.widget, 0, 1, 1, 1)
        content_presenter = StackPresenter(self.content_stack, content_view)
        self._destroy_funcs.append(content_presenter.destroy)

        header_view = HeaderView()
        body.attach(header_view.widget, 0, 0, 1, 1)
        header_presenter = HeaderPresenter(self._main_mod, header_view)
        self._destroy_funcs.append(header_presenter.destroy)

    def _hdl_window_delete_event(self, window: Gtk.Window, data: Gdk.Event):
        # Change active speaker key to None, this tells App to end the application.
        self._loop.create_task(self._main_mod.activate_speaker_by_key(None))

        # Return True to prevent the window from closing.
        return True

    @property
    def content_stack(self) -> StackModel:
        return self._content_stack

    def destroy(self) -> None:
        for f in self._destroy_funcs:
            f()


class DefaultAppGUIFactory(AppGUIFactory):
    def create(self, main_mod: Moderator, content_stack: StackModel) -> DefaultAppGUI:
        return DefaultAppGUI(main_mod, content_stack)
