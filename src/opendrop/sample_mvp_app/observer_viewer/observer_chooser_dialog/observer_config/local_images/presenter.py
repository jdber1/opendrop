from typing import Tuple

from opendrop.mvp.IView import IView
from opendrop.mvp.Presenter import Presenter
from opendrop.sample_mvp_app.observer_viewer.observer_chooser_dialog.observer_config.base_config.model import ObserverConfigRequest


class ImagesConfigIView(IView):
    pass


class ImagesConfigPresenter(Presenter[ObserverConfigRequest, ImagesConfigIView]):
    def setup(self):
        self.model.type = self.view.OBSERVER_TYPE

        self._frame_interval = 10  # type: int

        self.model.opts['image_paths'] = tuple()
        self.model.opts['timestamps'] = []

        self.view.set_frame_interval_input(self.frame_interval)

        self.view.events.on_file_input_changed.connect(self.handle_file_input_changed)
        self.view.events.on_frame_interval_input_changed.connect(self.handle_frame_interval_input_changed)

    def update_model_timestamps(self):
        self.model.opts['timestamps'] = [i * self.frame_interval for i in range(len(self.model.opts['image_paths']))]

    def handle_file_input_changed(self, filenames: Tuple[str]) -> None:
        self.model.opts['image_paths'] = filenames

        self.update_model_timestamps()

    def handle_frame_interval_input_changed(self, interval: int) -> None:
        self.frame_interval = interval

    @property
    def frame_interval(self) -> int:
        return self._frame_interval

    @frame_interval.setter
    def frame_interval(self, value: int) -> None:
        self._frame_interval = value

        self.update_model_timestamps()
