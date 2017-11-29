from typing import Any

from opendrop.mvp import handles
from opendrop.mvp.Presenter import Presenter

from opendrop.sample_mvp_app.presenters.IMainView import IMainView

from opendrop.sample_mvp_app.views.TimerExampleView import TimerExampleView
from opendrop.sample_mvp_app.views.BurgerExampleView import BurgerExampleView


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
