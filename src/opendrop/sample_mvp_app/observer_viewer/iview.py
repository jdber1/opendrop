from abc import abstractmethod
from typing import Optional

from opendrop.mvp.IView import IView
from opendrop.observer.bases import ObserverPreview


class IObserverViewerView(IView):
    @abstractmethod
    def set_viewer_preview(self, preview: Optional[ObserverPreview]) -> None: pass
