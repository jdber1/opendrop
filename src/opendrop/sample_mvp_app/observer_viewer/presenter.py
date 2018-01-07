from typing import Optional, Mapping, Any

from opendrop.sample_mvp_app.observer_viewer.model import ObserverViewerModel

from opendrop.mvp import handles
from opendrop.mvp.Presenter import Presenter
from opendrop.observer.bases import ObserverPreview
from opendrop.sample_mvp_app.observer_viewer.iview import IObserverViewerView
from opendrop.sample_mvp_app.observer_viewer.observer_chooser_dialog.view import \
    CameraChooserDialogView


class ObserverViewerPresenter(Presenter[ObserverViewerModel, IObserverViewerView]):
    def setup(self) -> None:
        self._active_preview = None  # type: Optional[ObserverPreview]

        self.observer_chosen = False  # type: bool

        self.do_observer_chooser()

    def do_observer_chooser(self) -> None:
        v = self.view.spawn(CameraChooserDialogView, model=self.model, child=True,
                            view_opts={'transient_for': self.view, 'modal': True})  # type: CameraChooserDialogView

        v.connect('on_submit', self._handle_observer_chooser_on_submit, once=True)

    def _handle_observer_chooser_on_submit(self, observer_type: Any, observer_opts: Mapping[str, Any]) -> None:
        if observer_type is None:
            if not self.observer_chosen:
                self.view.spawn(self.view.PREVIOUS)
                self.view.close()

            return

        self.observer_chosen = True
        self.model.current_observer = self.model.observer_service.get(observer_type, **observer_opts)

    def clear_active_preview(self):
        if self.active_preview is not None:
            self.active_preview.close()

            self.active_preview = None

    def teardown(self) -> None:
        self.clear_active_preview()

    @property
    def active_preview(self) -> Optional[ObserverPreview]:
        return self._active_preview

    @active_preview.setter
    def active_preview(self, value: Optional[ObserverPreview]) -> None:
        self._active_preview = value

        if not self.view.destroyed:
            self.view.set_viewer_preview(value)

    @handles('model', 'on_current_observer_changed')
    def handle_current_observer_changed(self) -> None:
        self.clear_active_preview()

        if self.model.current_observer is not None:
            self.active_preview = self.model.current_observer.preview()
