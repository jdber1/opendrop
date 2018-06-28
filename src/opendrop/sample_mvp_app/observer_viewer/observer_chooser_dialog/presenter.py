from typing import Any, List, Optional

from opendrop.mvp.Model import Model
from opendrop.mvp.Presenter import Presenter
from opendrop.mvp.View import View
from opendrop.observer.bases import ObserverType
from opendrop.sample_mvp_app.observer_viewer.model import ObserverViewerModel
from opendrop.sample_mvp_app.observer_viewer.observer_chooser_dialog.iview import \
    ICameraChooserDialogView
from opendrop.sample_mvp_app.observer_viewer.observer_chooser_dialog.observer_config.base_config.view import \
    ObserverConfigView


class ObserverConfigRequest(Model):
    def __init__(self):
        super().__init__()

        self.setup()

    def setup(self):
        self.type = None  # type: Optional[ObserverType]
        self.opts = {}

    def reset(self):
        self.setup()


class CameraChooserDialogPresenter(Presenter[ObserverViewerModel, ICameraChooserDialogView]):
    def setup(self):
        self.otypes = self.model.observer_types.get_types()  # type: List[Any]

        for i, otype in enumerate(self.otypes):
            self.view.add_observer_type(str(i), otype.display)

        self.config_view = None  # type: Optional[View]
        self.config_request = ObserverConfigRequest()  # type: ObserverConfigRequest

        self.view.events.on_type_combo_changed.connect(self.handle_type_combo_changed)
        self.view.events.on_submit_button_clicked.connect(self.handle_submit_button_clicked)
        self.view.events.on_cancel_button_clicked.connect(self.handle_cancel_button_clicked)
        self.view.events.on_request_close.connect(self.handle_request_close)

    def handle_type_combo_changed(self, active_id: str):
        otype = self.otypes[int(active_id)]  # type: Any

        config_view_cls = ObserverConfigView.get_view_for(otype)

        if self.config_view is not None:
            self.config_view.close()

        self.config_request.reset()

        self.config_view = self.view.spawn(config_view_cls, model=self.config_request, child=True)

        self.view.set_config(self.config_view)

    def handle_submit_button_clicked(self):
        self.view.submit(self.config_request.type, self.config_request.opts)
        self.view.close()

    def handle_cancel_button_clicked(self):
        self.view.events.on_request_close.fire()

    def handle_request_close(self):
        self.view.submit(None, {})
        self.view.close()
