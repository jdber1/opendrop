from gi.repository import Gtk

from injector import inject
from opendrop.appfw import component, Presenter
from opendrop.app.services.app import OpendropService


@component(
    template_path='./main_menu.ui',
)
class MainMenuPresenter(Presenter[Gtk.Window]):
    @inject
    def __init__(self, app_service: OpendropService) -> None:
        self.app_service = app_service

    def hdl_ift_btn_clicked(self, button: Gtk.Button) -> None:
        self.app_service.goto_ift()

    def hdl_conan_btn_clicked(self, button: Gtk.Button) -> None:
        self.app_service.goto_conan()
