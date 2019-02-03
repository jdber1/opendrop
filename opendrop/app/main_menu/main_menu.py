import asyncio
from typing import Optional

import pkg_resources
from gi.repository import Gtk, GdkPixbuf, Gio, GLib

from opendrop.app.app import AppSpeakerID
from opendrop.component.gtk_widget_view import GtkWidgetView
from opendrop.component.stack import StackModel
from opendrop.utility.events import Event
from opendrop.utility.speaker import Speaker, Moderator


class MainMenuView(GtkWidgetView[Gtk.Grid]):
    IFT_BUTTON_IMAGE = GdkPixbuf.Pixbuf.new_from_stream(
        Gio.MemoryInputStream.new_from_bytes(
            GLib.Bytes(
                pkg_resources.resource_stream('opendrop.res', 'images/ift_btn.png').read() )))

    CONAN_BUTTON_IMAGE = GdkPixbuf.Pixbuf.new_from_stream(
        Gio.MemoryInputStream.new_from_bytes(
            GLib.Bytes(
                pkg_resources.resource_stream('opendrop.res', 'images/conan_btn.png').read() )))

    def __init__(self) -> None:
        self.on_ift_btn_clicked = Event()
        self.on_conan_btn_clicked = Event()

        self.widget = Gtk.Grid()

        ift_btn = Gtk.Button(label='Interfacial Tension', hexpand=True, vexpand=True)
        self.widget.attach(ift_btn, 0, 0, 1, 1)

        conan_btn = Gtk.Button(label='Contact Angle', hexpand=True, vexpand=True)
        self.widget.attach(conan_btn, 0, 1, 1, 1)

        ift_btn_image_pixbuf = self.IFT_BUTTON_IMAGE.scale_simple(
            dest_width=64,
            dest_height=64/self.IFT_BUTTON_IMAGE.props.width * self.IFT_BUTTON_IMAGE.props.height,
            interp_type=GdkPixbuf.InterpType.BILINEAR)

        ift_btn_image = Gtk.Image(pixbuf=ift_btn_image_pixbuf, margin=16)
        ift_btn.set_image(ift_btn_image)
        ift_btn.set_always_show_image(True)
        ift_btn.set_image_position(Gtk.PositionType.TOP)

        conan_btn_image_pixbuf = self.CONAN_BUTTON_IMAGE.scale_simple(
            dest_width=64,
            dest_height=64/self.CONAN_BUTTON_IMAGE.props.width * self.CONAN_BUTTON_IMAGE.props.height,
            interp_type=GdkPixbuf.InterpType.BILINEAR)

        conan_btn_image = Gtk.Image(pixbuf=conan_btn_image_pixbuf, margin=16)
        conan_btn.set_image(conan_btn_image)
        conan_btn.set_always_show_image(True)
        conan_btn.set_image_position(Gtk.PositionType.TOP)

        ift_btn.connect('clicked', lambda *_: self.on_ift_btn_clicked.fire())
        conan_btn.connect('clicked', lambda *_: self.on_conan_btn_clicked.fire())

        self.widget.show_all()


class MainMenuPresenter:
    def __init__(self, main_mod: Moderator, view: MainMenuView):
        self._loop = asyncio.get_event_loop()
        self._main_mod = main_mod
        self._view = view

        self.__event_connections = [
            self._view.on_ift_btn_clicked.connect(self.hdl_view_ift_btn_clicked),
            self._view.on_conan_btn_clicked.connect(self.hdl_view_conan_btn_clicked)
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
