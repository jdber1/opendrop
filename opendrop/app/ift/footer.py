import asyncio
from typing import Sequence, TypeVar, Generic, Optional

from gi.repository import Gtk, Gdk

from opendrop.component.gtk_widget_view import GtkWidgetView
from opendrop.utility.events import Event
from opendrop.utility.speaker import Moderator


class FooterView(GtkWidgetView[Gtk.Box]):
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


SomeWizardPageID = TypeVar('SpecificWizardPageID')


class FooterPresenter(Generic[SomeWizardPageID]):
    def __init__(self, wizard_mod: Moderator[SomeWizardPageID], page_order: Sequence[SomeWizardPageID],
                 view: FooterView) -> None:
        self._loop = asyncio.get_event_loop()

        self._wizard_mod = wizard_mod
        self._page_order = page_order
        self._view = view

        self.__event_connections = [
            self._view.on_next_btn_clicked.connect(self._hdl_view_next_btn_clicked, immediate=True),
            self._view.on_back_btn_clicked.connect(self._hdl_view_back_btn_clicked, immediate=True)
        ]

    def _hdl_view_next_btn_clicked(self) -> None:
        next_page_id = self._get_next_page_id()

        if next_page_id is None:
            return

        self._loop.create_task(self._wizard_mod.activate_speaker_by_key(next_page_id))

    def _hdl_view_back_btn_clicked(self) -> None:
        prev_page_id = self._get_prev_page_id()

        if prev_page_id is None:
            return

        self._loop.create_task(self._wizard_mod.activate_speaker_by_key(prev_page_id))

    def _get_next_page_id(self) -> Optional[SomeWizardPageID]:
        current_page_id = self._wizard_mod.active_speaker_key
        assert current_page_id is not None
        current_page_order_index = self._page_order.index(current_page_id)
        next_page_order_index = current_page_order_index + 1

        try:
            return self._page_order[next_page_order_index]
        except IndexError:
            return None

    def _get_prev_page_id(self) -> Optional[SomeWizardPageID]:
        current_page_id = self._wizard_mod.active_speaker_key
        assert current_page_id is not None
        current_page_order_index = self._page_order.index(current_page_id)
        prev_page_order_index = current_page_order_index - 1

        if prev_page_order_index < 0:
            return None

        return self._page_order[prev_page_order_index]

    def destroy(self) -> None:
        for ec in self.__event_connections:
            ec.disconnect()
