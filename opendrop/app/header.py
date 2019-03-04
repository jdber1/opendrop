import asyncio

import pkg_resources
from gi.repository import Gio, Gtk, GdkPixbuf, GLib

from opendrop.app.app_speaker_id import AppSpeakerID
from opendrop.component.gtk_widget_view import GtkWidgetView
from opendrop.utility.bindable import AtomicBindable
from opendrop.utility.bindable.atomic_binding_mitm import AtomicBindingMITM
from opendrop.utility.bindable.binding import Binding
from opendrop.utility.bindablegext.bindable import GObjectPropertyBindable
from opendrop.utility.events import Event
from opendrop.utility.speaker import Moderator


class HeaderView(GtkWidgetView[Gtk.Grid]):
    LOGO_WIDE_PIXBUF = GdkPixbuf.Pixbuf.new_from_stream(
        Gio.MemoryInputStream.new_from_bytes(
            GLib.Bytes(
                pkg_resources.resource_stream('opendrop.res', 'images/logo_wide.png').read() )))

    def __init__(self) -> None:
        self.widget = Gtk.HeaderBar(hexpand=True)

        self.on_return_to_menu_btn_clicked = Event()

        logo_pixbuf = self.LOGO_WIDE_PIXBUF.scale_simple(
            dest_width=100,
            dest_height=100/self.LOGO_WIDE_PIXBUF.props.width * self.LOGO_WIDE_PIXBUF.props.height,
            interp_type=GdkPixbuf.InterpType.BILINEAR)
        logo_wgt = Gtk.Image(pixbuf=logo_pixbuf, margin=5)
        self.widget.pack_start(logo_wgt)

        return_to_menu_btn = Gtk.Button(label='Return to menu')
        self.widget.pack_end(return_to_menu_btn)
        return_to_menu_btn.connect('clicked', lambda *_: self.on_return_to_menu_btn_clicked.fire())

        self.bn_header_title = GObjectPropertyBindable(self.widget, 'title')  # type: AtomicBindable[str]
        self.bn_return_to_menu_btn_visible = GObjectPropertyBindable(return_to_menu_btn, 'visible')  # type: AtomicBindable[bool]


class HeaderPresenter:
    def __init__(self, main_mod: Moderator[AppSpeakerID], view: HeaderView) -> None:
        self._loop = asyncio.get_event_loop()
        self._main_mod = main_mod
        self._view = view

        self.__event_connections = [
            self._view.on_return_to_menu_btn_clicked.connect(self.hdl_view_return_to_menu_btn_clicked)
        ]

        self.__data_bindings = [
            Binding(self._main_mod.bn_active_speaker_key, self._view.bn_header_title,
                    mitm=AtomicBindingMITM(to_dst=lambda key: key.header_title if key is not None else '')),
            Binding(self._main_mod.bn_active_speaker_key, self._view.bn_return_to_menu_btn_visible,
                    mitm=AtomicBindingMITM(to_dst=lambda key: key is not AppSpeakerID.MAIN_MENU))
        ]

    def hdl_view_return_to_menu_btn_clicked(self) -> None:
        self._loop.create_task(self._main_mod.activate_speaker_by_key(AppSpeakerID.MAIN_MENU))

    def destroy(self) -> None:
        for ec in self.__event_connections:
            ec.disconnect()

        for db in self.__data_bindings:
            db.unbind()
