from gi.repository import Gtk

from opendrop.observer.gtk.preview_viewer_controller import AbstractPreviewViewerController, \
    PreviewViewerControllerCore, PreviewViewer
from opendrop.observer.types.camera import CameraObserverPreview


class CameraObserverPreviewViewerController(AbstractPreviewViewerController, PreviewViewerControllerCore):
    def __init__(self, **properties):
        super().__init__(**properties)

        # Attributes
        self._preview_index = 0  # type: int

        # Setup properties
        self.props.margin = 5

        self.props.column_spacing = 5
        self.props.row_spacing = 5

        # Build widget
        self.attach(Gtk.Label('Live preview'), 0, 0, 1, 1)

        self.show_all()

    @staticmethod
    def can_control(viewer: 'PreviewViewer') -> bool:
        return isinstance(viewer.props.preview, CameraObserverPreview)
