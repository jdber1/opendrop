import asyncio
from typing import Optional

from gi.repository import Gtk

from opendrop.app.app import AppSpeakerID
from opendrop.component.gtk_widget_view import GtkWidgetView
from opendrop.component.stack import StackModel
from opendrop.utility.events import Event
from opendrop.utility.speaker import Speaker, Moderator


class MainMenuView(GtkWidgetView[Gtk.Grid]):
    def __init__(self) -> None:
        self.on_ift_btn_clicked = Event()
        self.on_conan_btn_clicked = Event()

        self.widget = Gtk.Grid()

        ift_btn = Gtk.Button(label='IFT')
        self.widget.attach(ift_btn, 0, 0, 1, 1)

        conan_btn = Gtk.Button(label='Contact Angle')
        self.widget.attach(conan_btn, 0, 1, 1, 1)

        ift_btn.connect('clicked', lambda *_: self.on_ift_btn_clicked.fire())
        conan_btn.connect('clicked', lambda *_: self.on_conan_btn_clicked.fire())

        self.widget.show_all()


class MainMenuPresenter:
    def __init__(self, main_mod: Moderator, view: MainMenuView):
        self._loop = asyncio.get_event_loop()
        self._main_mod = main_mod
        self._view = view

        self.__event_connections = [
            self._view.on_ift_btn_clicked.connect(self.hdl_view_ift_btn_clicked, immediate=True),
            self._view.on_conan_btn_clicked.connect(self.hdl_view_conan_btn_clicked, immediate=True)
        ]

    def hdl_view_ift_btn_clicked(self) -> None:
        self._loop.create_task(self._main_mod.activate_speaker_by_key(AppSpeakerID.IFT))

    def hdl_view_conan_btn_clicked(self) -> None:
        self._loop.create_task(self._main_mod.activate_speaker_by_key(AppSpeakerID.CONAN))

    def destroy(self) -> None:
        for ec in self.__event_connections:
            ec.disconnect()


class MainMenuSpeaker(Speaker):
    def __init__(self, content_stack: StackModel) -> None:
        super().__init__()

        self._main_menu_presenter = None  # type: Optional[MainMenuPresenter]

        self._content_stack = content_stack

        self._main_menu_view = MainMenuView()
        self._main_menu_view_key = object()

        content_stack.add_child(self._main_menu_view_key, self._main_menu_view)

    def do_activate(self):
        self._main_menu_presenter = MainMenuPresenter(self.moderator, self._main_menu_view)
        self._content_stack.visible_child_key = self._main_menu_view_key

    def do_deactivate(self) -> None:
        self._main_menu_presenter.destroy()
