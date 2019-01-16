import asyncio
import warnings
from abc import abstractmethod, ABC

from gi.repository import Gtk, Gdk

from opendrop.app.app_speaker_id import AppSpeakerID
from opendrop.app.header import HeaderView, HeaderPresenter
from opendrop.component.gtk_widget_view import GtkWidgetView
from opendrop.component.stack import StackModel, StackView, StackPresenter
from opendrop.utility.events import Event
from opendrop.utility.speaker import Moderator, Speaker


class AppSpeakerFactory(ABC):
    @abstractmethod
    def set_content_stack(self, content_stack: StackModel) -> None:
        """Set `content_stack` as the main content stack model to be used by the speakers."""

    @abstractmethod
    def create_for_key(self, key: AppSpeakerID) -> Speaker:
        """Provide the speaker that will be identified by `key`"""


class AppView(GtkWidgetView[Gtk.Window]):
    def __init__(self) -> None:
        self.widget = Gtk.Window()

        body = Gtk.Grid()
        self.widget.add(body)

        self.content_view = StackView()
        body.attach(self.content_view.widget, 0, 1, 1, 1)

        self.header_view = HeaderView()
        body.attach(self.header_view.widget, 0, 0, 1, 1)

        self.widget.show_all()

        self.on_request_close_window = Event()
        self.widget.connect('delete-event', self._hdl_window_delete_event)

    def _hdl_window_delete_event(self, window: Gtk.Window, data: Gdk.Event) -> bool:
        self.on_request_close_window.fire()

        # Return True to prevent the window from closing.
        return True

    def destroy(self) -> None:
        self.widget.destroy()


class AppPresenter:
    def __init__(self, main_mod: Moderator, content_stack: StackModel, view: AppView) -> None:
        self._loop = asyncio.get_event_loop()

        self._main_mod = main_mod
        self._content_stack = content_stack
        self._view = view

        self._content_presenter = StackPresenter(self._content_stack, self._view.content_view)
        self._header_presenter = HeaderPresenter(self._main_mod, self._view.header_view)

        self.__event_connections = [
            self._view.on_request_close_window.connect(self._hdl_view_request_close_window)
        ]

    def _hdl_view_request_close_window(self) -> None:
        # Change active speaker key to None, this tells App to end the application.
        self._loop.create_task(
            self._main_mod.activate_speaker_by_key(None)
        )

    def destroy(self) -> None:
        self._content_presenter.destroy()
        self._header_presenter.destroy()

        for ec in self.__event_connections:
            ec.disconnect()


class App:
    def __init__(self, speaker_factory: AppSpeakerFactory) -> None:
        self._loop = asyncio.get_event_loop()

        self._main_mod = Moderator()
        self._content_stack = StackModel()

        self._app_view = AppView()
        self._app_presenter = AppPresenter(self._main_mod, self._content_stack, self._app_view)

        speaker_factory.set_content_stack(self._content_stack)
        for key in AppSpeakerID:
            speaker = speaker_factory.create_for_key(key)
            if speaker is None:
                warnings.warn('No speaker created for key `{}`, ignoring.'.format(key))
                continue

            self._main_mod.add_speaker(key, speaker)

        self._main_mod.bn_active_speaker_key.on_changed.connect(self._hdl_main_mod_active_speaker_key_changed)

    def _hdl_main_mod_active_speaker_key_changed(self) -> None:
        if self._main_mod.active_speaker_key is None:
            self.destroy()

    def run(self) -> None:
        self._loop.create_task(self._main_mod.activate_speaker_by_key(AppSpeakerID.MAIN_MENU))
        self._loop.run_forever()

    def destroy(self) -> None:
        self._app_presenter.destroy()
        self._app_view.destroy()
        self._loop.stop()
