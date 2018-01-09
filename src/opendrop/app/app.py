from opendrop import app
from opendrop.gtk_specific.GtkApplication import GtkApplication


class OpendropApplication(GtkApplication):
    APPLICATION_ID = 'com.github.jdber1.opendrop'

    PRESENTERS_PKG = app

    def main(self) -> None:
        # self.spawn(view_cls=..., model=...)
        pass
