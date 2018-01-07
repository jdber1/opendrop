from opendrop.mvp.Model import Model
from opendrop.sample_mvp_app.burger_example.model import BurgerOrder
from opendrop.sample_mvp_app.observer_viewer.model import ObserverViewerModel


class MainMenuModel(Model):
    def __init__(self):
        super().__init__()

        self.burger_order = BurgerOrder()  # type: BurgerOrder

    @staticmethod
    def new_camera_viewer_model() -> ObserverViewerModel:
        return ObserverViewerModel()

    def get_burger_order(self):
        return self.burger_order
