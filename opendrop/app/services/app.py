from gi.repository import GObject


class OpendropService(GObject.Object):
    def goto_main_menu(self) -> None:
        self.main_menu.emit()

    def goto_ift(self) -> None:
        self.ift.emit()

    def goto_conan(self) -> None:
        self.conan.emit()

    def quit(self) -> None:
        self.quit.emit()

    @GObject.Signal
    def main_menu(self) -> None:
        pass

    @GObject.Signal
    def ift(self) -> None:
        pass

    @GObject.Signal
    def conan(self) -> None:
        pass

    @GObject.Signal
    def quit(self) -> None:
        pass
