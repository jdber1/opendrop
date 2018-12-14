import asyncio

from gi.repository import Gtk

from opendrop.gtk_specific.stack import StackModel, StackView, StackPresenter
from opendrop.mytypes import Destroyable
from opendrop.utility.speaker import Moderator


class HeaderView:
    pass


class HeaderPresenter:
    pass


class AppUI:
    def __init__(self, main_mod: Moderator):
        self._window = Gtk.Window()
        self.content_model = StackModel()

        self._content_view = StackView()
        self._content_presenter = StackPresenter(self.content_model, self._content_view)

    def destroy(self) -> None:
        self._window.destroy()


class App:
    def __init__(self) -> None:
        self.main_mod = Moderator()
        self._ui = AppUI(self.main_mod)  # type: Destroyable

    def run(self) -> None:
        asyncio.get_event_loop()