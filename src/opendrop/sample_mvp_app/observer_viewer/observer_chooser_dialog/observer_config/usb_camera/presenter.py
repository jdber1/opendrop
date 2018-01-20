from opendrop.mvp.IView import IView
from opendrop.mvp.Presenter import Presenter
from opendrop.sample_mvp_app.observer_viewer.observer_chooser_dialog.observer_config.base_config.model import ObserverConfigRequest
from opendrop.utility.events import handler


class USBCameraConfigIView(IView):
    pass


class USBCameraConfigPresenter(Presenter[ObserverConfigRequest, USBCameraConfigIView]):
    DEFAULT_CAMERA_INDEX = 0

    def setup(self):
        self.model.type = self.view.OBSERVER_TYPE
        self.model.opts['camera_index'] = self.DEFAULT_CAMERA_INDEX

        self.view.set_camera_index(self.model.opts['camera_index'])

    @handler('view', 'on_camera_index_changed')
    def handle_camera_index_changed(self, index: int) -> None:
        self.model.opts['camera_index'] = index
