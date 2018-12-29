import asyncio

from gi.repository import Gtk, GdkPixbuf

from opendrop.app.app_speaker_id import AppSpeakerID
from opendrop.component.gtk_widget_view import GtkWidgetView
from opendrop.res import res
from opendrop.utility.bindable.bindable import AtomicBindableAdapter, BaseAtomicBindable
from opendrop.utility.bindable.binding import Binding, AtomicBindingMITM
from opendrop.utility.bindablegext.bindable import link_atomic_bn_adapter_to_g_prop
from opendrop.utility.events import Event
from opendrop.utility.speaker import Moderator


class HeaderView(GtkWidgetView[Gtk.Grid]):
    def __init__(self) -> None:
        self.widget = Gtk.HeaderBar(hexpand=True)

        self.bn_header_title = AtomicBindableAdapter()  # type: AtomicBindableAdapter[str]
        self.bn_return_to_menu_btn_visible = AtomicBindableAdapter()  # type: AtomicBindableAdapter[bool]

        self.on_return_to_menu_btn_clicked = Event()

        link_atomic_bn_adapter_to_g_prop(self.bn_header_title, self.widget, 'title')

        logo_path = res/'images'/'logo_wide.png'
        logo_pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(str(logo_path), width=100, height=-1)
        logo_wgt = Gtk.Image(pixbuf=logo_pixbuf, margin=5)
        self.widget.pack_start(logo_wgt)

        return_to_menu_btn = Gtk.Button(label='Return to menu')
        self.widget.pack_end(return_to_menu_btn)
        return_to_menu_btn.connect('clicked', lambda *_: self.on_return_to_menu_btn_clicked.fire())
        link_atomic_bn_adapter_to_g_prop(self.bn_return_to_menu_btn_visible, return_to_menu_btn, 'visible')


class HeaderPresenter:
    def __init__(self, main_mod: Moderator[AppSpeakerID], view: HeaderView) -> None:
        self._loop = asyncio.get_event_loop()
        self._main_mod = main_mod
        self._view = view

        self.__event_connections = [
            self._view.on_return_to_menu_btn_clicked.connect(self.hdl_view_return_to_menu_btn_clicked, immediate=True)
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
