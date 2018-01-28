from abc import abstractmethod
from typing import Optional, Type

from gi.repository import Gtk, GObject

from opendrop.observer.gtk.preview_viewer import PreviewViewer


class PreviewViewerControllerCore:
    @classmethod
    def get_implementation_for(cls, pv: PreviewViewer) -> Type['AbstractPreviewViewerController']:
        for sub in cls.__subclasses__():
            if sub.can_control(pv):
                return sub
        else:
            raise ValueError('Couldn\'t find an implementation for {!r} (with preview {!r}).'.format(pv, pv.props.preview))

    @staticmethod
    @abstractmethod
    def can_control(viewer: Optional[PreviewViewer]) -> bool: pass


class AbstractPreviewViewerController(Gtk.Grid):
    def __init__(self, **properties):
        self._viewer = None  # type: Optional[PreviewViewer]

        super().__init__(**properties)


    @GObject.property
    def viewer(self) -> PreviewViewer:
        return self._viewer

    @viewer.setter
    def viewer(self, value: PreviewViewer) -> None:
        self._viewer = value


class NoPreviewViewerController(AbstractPreviewViewerController, PreviewViewerControllerCore):
    @staticmethod
    def can_control(viewer: PreviewViewer) -> bool:
        return viewer.props.preview is None


class PreviewViewerController(AbstractPreviewViewerController):
    __gtype_name__ = 'PreviewViewerController'

    def __init__(self, viewer: Optional[PreviewViewer] = None, **properties):
        super().__init__(**properties)

        # Attributes
        self._pvc = None  # type: Optional[AbstractPreviewViewerController]

        # Styles
        self.get_style_context().add_class('gray-box')

        css = Gtk.CssProvider()  # type: Gtk.CssProvider
        css.load_from_data(bytes('''
            .gray-box {
                background-color: gainsboro;
            }
        ''', encoding='utf-8'))

        self.get_style_context().add_provider(css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        # Build widget
        inner = Gtk.Grid(margin=5, column_spacing=5, row_spacing=5)
        self.attach(inner, 0, 0, 1, 1)

        zoom_btn_container = Gtk.Grid()  # type: Gtk.Grid
        inner.attach(zoom_btn_container, 1, 0, 1, 1)

        zoom_btn_lbl = Gtk.Label('Zoom:')  # type: Gtk.Label
        zoom_btn_container.attach(zoom_btn_lbl, 0, 0, 1, 1)

        self.zoom_btn = Gtk.Button()  # type: Gtk.Button
        zoom_btn_container.attach(self.zoom_btn, 0, 2, 1, 1)

        self.zoom_btn.connect('clicked', self.handle_zoom_btn_clicked)

        # Blank space widget
        inner.attach(Gtk.Box(hexpand=True), 0, 1, 1, 1)
        #

        # PreviewViewerControllerCore area
        self.pvc_area = Gtk.Box(valign=Gtk.Align.CENTER)
        inner.attach(self.pvc_area, 0, 0, 1, 1)
        #

        self.show_all()

        # Invoke setters
        self.viewer = viewer
        #

        self.update_controls()

    def handle_zoom_btn_clicked(self, zoom_btn: Gtk.Widget) -> None:
        if self.viewer is None:
            return

        self.viewer.props.zoom = self.viewer.props.zoom.next()

    def update_controls(self) -> None:
        if self._pvc is not None and self._pvc.can_control(self.viewer):
            # Existing viewer controller is still compatible with current viewer, do nothing
            return

        for c in self.pvc_area.get_children():
            c.destroy()

        if self.viewer is None:
            return

        pvc_cls = PreviewViewerControllerCore.get_implementation_for(self.viewer)

        self._pvc = pvc_cls(viewer=self.viewer)
        self._pvc.show()

        self.pvc_area.add(self._pvc)

    viewer = GObject.Property(AbstractPreviewViewerController.viewer.fget)

    def _handle_viewer_notify_zoom(self, viewer: PreviewViewer, param) -> None:
        self.zoom_btn.props.label = str(viewer.props.zoom.next())

    def _handle_viewer_notify_preview(self, viewer: PreviewViewer, param) -> None:
        self.update_controls()

    def _connect_to_viewer(self) -> None:
        self.viewer.connect('notify::zoom', self._handle_viewer_notify_zoom)
        self.viewer.connect('notify::preview', self._handle_viewer_notify_preview)

    def _disconnect_from_viewer(self) -> None:
        self.viewer.disconnect_by_func(self._handle_viewer_notify_zoom)
        self.viewer.disconnect_by_func(self._handle_viewer_notify_preview)

    def _poke_viewer(self) -> None:
        self.viewer.props.zoom = self.viewer.props.zoom

    @viewer.setter
    def viewer(self, value: PreviewViewer) -> None:
        if self.viewer is not None:
            self._disconnect_from_viewer()

        AbstractPreviewViewerController.viewer.fset(self, value)

        self._connect_to_viewer()
        self._poke_viewer()

        self.update_controls()
