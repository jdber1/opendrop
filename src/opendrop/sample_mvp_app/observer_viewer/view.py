from typing import Optional

from opendrop.gtk_specific.GtkWindowView import GtkWindowView
from opendrop.observer.bases import ObserverPreview
from opendrop.sample_mvp_app.observer_viewer.iview import IObserverViewerView
from opendrop.widgets.observer.preview_viewer import PreviewViewer


class ObserverViewerView(GtkWindowView, IObserverViewerView):
    def setup(self) -> None:
        self.hidden = True

        # -- Build UI --
        viewer = PreviewViewer()

        self.window.add(viewer)

        viewer.show()

        # -- Keep these widgets accessible --
        self.viewer = viewer

    def set_viewer_preview(self, preview: Optional[ObserverPreview]):
        self.viewer.set_preview(preview)

        self.hidden = False

