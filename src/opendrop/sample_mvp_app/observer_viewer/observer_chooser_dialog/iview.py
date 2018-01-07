from abc import abstractmethod
from typing import Mapping, Any

from opendrop.mvp.IView import IView


class ICameraChooserDialogView(IView):
    @abstractmethod
    def add_observer_type(self, id: Any, name: str) -> None: pass

    @abstractmethod
    def submit(self, observer_type: Any, observer_opts: Mapping[str, Any]) -> None: pass