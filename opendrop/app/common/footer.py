import asyncio
from typing import Optional, Callable

from gi.repository import Gtk, Gdk

from opendrop.component.gtk_widget_view import GtkWidgetView
from opendrop.utility.bindable.bindable import AtomicBindableAdapter
from opendrop.utility.bindablegext.bindable import link_atomic_bn_adapter_to_g_prop
from opendrop.utility.events import Event


class LinearNavigatorFooterView(GtkWidgetView[Gtk.Box]):
    STYLE = '''
    .footer-nav-btn {
         min-height: 0px;
         min-width: 60px;
         padding: 8px 4px 8px 4px;
    }
    '''

    _STYLE_PROV = Gtk.CssProvider()
    _STYLE_PROV.load_from_data(bytes(STYLE, 'utf-8'))
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), _STYLE_PROV, Gtk.STYLE_PROVIDER_PRIORITY_USER)

    def __init__(self) -> None:
        self.widget = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, margin=10)
        back_btn = Gtk.Button('< Back')
        back_btn.get_style_context().add_class('footer-nav-btn')
        self.widget.pack_start(back_btn, expand=False, fill=False, padding=0)

        next_btn = Gtk.Button('Next >')
        next_btn.get_style_context().add_class('footer-nav-btn')
        self.widget.pack_end(next_btn, expand=False, fill=False, padding=0)
        self.widget.show_all()

        self.on_next_btn_clicked = Event()
        next_btn.connect('clicked', lambda *_: self.on_next_btn_clicked.fire())

        self.on_back_btn_clicked = Event()
        back_btn.connect('clicked', lambda *_: self.on_back_btn_clicked.fire())

        self.bn_back_btn_visible = AtomicBindableAdapter()
        self.bn_next_btn_visible = AtomicBindableAdapter()

        link_atomic_bn_adapter_to_g_prop(self.bn_back_btn_visible, back_btn, 'visible')
        link_atomic_bn_adapter_to_g_prop(self.bn_next_btn_visible, next_btn, 'visible')


class LinearNavigatorFooterPresenter:
    def __init__(self, back: Optional[Callable], next: Optional[Callable], view: LinearNavigatorFooterView) -> None:
        self._loop = asyncio.get_event_loop()

        self._back = back
        self._next = next

        self._view = view

        self.__event_connections = [
            self._view.on_next_btn_clicked.connect(self._hdl_view_next_btn_clicked, immediate=True),
            self._view.on_back_btn_clicked.connect(self._hdl_view_back_btn_clicked, immediate=True)
        ]

        self._update_view_nav_buttons_visibility()

    def _hdl_view_back_btn_clicked(self) -> None:
        self._back()

    def _hdl_view_next_btn_clicked(self) -> None:
        self._next()

    def _update_view_nav_buttons_visibility(self) -> None:
        self._view.bn_back_btn_visible.set(self._back is not None)
        self._view.bn_next_btn_visible.set(self._next is not None)

    def destroy(self) -> None:
        for ec in self.__event_connections:
            ec.disconnect()


class LinearNavigatorFooter:
    def __init__(self, *, back: Optional[Callable] = None, next: Optional[Callable] = None) -> None:
        self._back = back
        self._next = next

        self._view = LinearNavigatorFooterView()
        self._presenter = None  # type: Optional[LinearNavigatorFooterPresenter]

    @property
    def view(self) -> GtkWidgetView:
        return self._view

    def activate(self) -> None:
        self._presenter = LinearNavigatorFooterPresenter(back=self._back, next=self._next, view=self._view)

    def deactivate(self) -> None:
        assert self._presenter is not None
        self._presenter.destroy()
        self._presenter = None
