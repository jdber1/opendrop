from opendrop import sample_mvp_app
from opendrop.gtk_specific.GtkApplication import GtkApplication
from opendrop.sample_mvp_app.main_menu.model import MainMenuModel
from opendrop.sample_mvp_app.main_menu.view import MainView


class SampleApplication(GtkApplication):
    APPLICATION_ID = 'org.example.sampleapp'

    PRESENTERS_PKG = sample_mvp_app

    ENTRY_VIEW = MainView

    def main(self) -> None:
        self.spawn(self.ENTRY_VIEW, MainMenuModel())
