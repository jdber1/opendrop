from opendrop.mvp.Presenter import Presenter
from opendrop.sample_mvp_app.burger_example.view import BurgerExampleView
from opendrop.sample_mvp_app.main_menu.iview import IMainView
from opendrop.sample_mvp_app.main_menu.model import MainMenuModel
from opendrop.sample_mvp_app.observer_viewer.view import ObserverViewerView
from opendrop.sample_mvp_app.timer_example.view import TimerExampleView
from opendrop.utility.events import handler


class MainPresenter(Presenter[MainMenuModel, IMainView]):
    @handler('view', 'on_timer_button_clicked')
    def handle_timer_button_clicked(self):
        self.view.spawn(TimerExampleView, view_opts={'transient_for': self.view, 'modal': True})
        self.view.close()

    @handler('view', 'on_burger_button_clicked')
    def handle_burger_button_clicked(self):
        burger_order = self.model.get_burger_order()
        self.view.spawn(BurgerExampleView, model=burger_order, child=True, view_opts={'transient_for': self.view, 'modal': False})

    @handler('view', 'on_camera_button_clicked')
    def handle_camera_button_clicked(self):
        self.view.spawn(ObserverViewerView, model=self.model.new_camera_viewer_model(), view_opts={'transient_for': self.view, 'modal': True})
        self.view.close()

    @handler('view', 'on_about_button_clicked')
    def handle_about_button_clicked(self):
        self.view.show_about_dialog()
