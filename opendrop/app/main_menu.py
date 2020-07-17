from gi.repository import Gtk, GObject

from opendrop.appfw import Presenter, component, install


@component(
    template_path='./main_menu.ui',
)
class MainMenuPresenter(Presenter[Gtk.Window]):
    def hdl_ift_btn_clicked(self, button: Gtk.Button) -> None:
        self.ift.emit()

    def hdl_conan_btn_clicked(self, button: Gtk.Button) -> None:
        self.conan.emit()

    @install
    @GObject.Signal
    def ift(self) -> None: pass

    @install
    @GObject.Signal
    def conan(self) -> None: pass
