from typing import Any

from opendrop.app.presenters.IMainView import IMainView
from opendrop.app.views.BurgerExampleView import BurgerExampleView
from opendrop.app.views.TimerExampleView import TimerExampleView

from opendrop.mvp import handles
from opendrop.mvp.Presenter import Presenter


class MainPresenter(Presenter[Any, IMainView]):
    @handles('on_timer_button_clicked')
    def handle_timer_button_clicked(self):
        self.view.close(next_view=TimerExampleView)

    @handles('on_burger_button_clicked')
    def handle_burger_button_clicked(self):
        self.view.close(next_view=BurgerExampleView)

    @handles('on_about_button_clicked')
    def handle_about_button_clicked(self):
        self.view.show_about_dialog()
