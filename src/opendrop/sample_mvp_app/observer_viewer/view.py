from typing import Optional

from gi.repository import Gtk

from opendrop.gtk_specific.GtkWindowView import GtkWindowView
from opendrop.observer.bases import ObserverPreview
from opendrop.observer.gtk import PreviewViewer, PreviewViewerController
from opendrop.sample_mvp_app.observer_viewer.iview import IObserverViewerView


class ObserverViewerView(GtkWindowView, IObserverViewerView):
    def setup(self) -> None:
        self.hidden = True

        # -- Build UI --
        body = Gtk.Grid()

        self.viewer = PreviewViewer(hexpand=True, vexpand=True)
        viewer_controller = PreviewViewerController(viewer=self.viewer)

        body.attach(self.viewer, 0, 0, 1, 1)
        body.attach(viewer_controller, 0, 1, 1, 1)

        self.window.add(body)

        body.show_all()

    def set_viewer_preview(self, preview: Optional[ObserverPreview]):
        self.viewer.props.preview = preview

        self.hidden = False

