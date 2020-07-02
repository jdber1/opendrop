from gi.repository import Gtk

from opendrop.appfw import Inject, component
from opendrop.app.services.app import OpendropService


@component(
    template_path='./main_menu.ui',
)
class MainMenu(Gtk.Window):
    __gtype_name__ = 'MainMenu'

    app_service = Inject(OpendropService)

    def hdl_ift_btn_clicked(self, button: Gtk.Button) -> None:
        self.app_service.goto_ift()

    def hdl_conan_btn_clicked(self, button: Gtk.Button) -> None:
        self.app_service.goto_conan()
