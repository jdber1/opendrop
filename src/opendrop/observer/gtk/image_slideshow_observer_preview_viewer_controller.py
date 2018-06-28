import math

from gi.repository import Gtk

from opendrop.observer.gtk.preview_viewer_controller import AbstractPreviewViewerController, \
    PreviewViewerControllerCore, PreviewViewer
from opendrop.observer.types.image_slideshow import ImageSlideshowObserverPreview
from opendrop.widgets.integer_entry import IntegerEntry


class ImageSlideshowObserverPreviewViewerController(AbstractPreviewViewerController, PreviewViewerControllerCore):
    def __init__(self, **properties):
        super().__init__(**properties)

        # Attributes
        self._preview_index = 0  # type: int

        # Setup properties
        self.props.column_spacing = 5
        self.props.row_spacing = 5

        # Build widget
        left_btn = Gtk.Button.new_from_icon_name('media-skip-backward', Gtk.IconSize.BUTTON)  # type: Gtk.Button
        left_btn.connect('clicked', self.handle_left_btn_clicked)

        self.attach(left_btn, 0, 0, 1, 1)

        num_images = self.viewer.props.preview.num_images  # type: int
        self.preview_index_input = IntegerEntry(min=1, max=num_images, default=0, width_chars=int(math.log10(num_images or 1)) + 1)
        self.preview_index_input.connect('changed', self.handle_preview_index_input_changed)

        self.attach(self.preview_index_input, 1, 0, 1, 1)

        total_images_label = Gtk.Label("of {}".format(self.viewer.props.preview.num_images))

        self.attach(total_images_label, 2, 0, 1, 1)

        right_btn = Gtk.Button.new_from_icon_name('media-skip-forward', Gtk.IconSize.BUTTON)  # type: Gtk.Button
        right_btn.connect('clicked', self.handle_right_btn_clicked)

        self.attach(right_btn, 3, 0, 1, 1)

        self.show_all()

        # Invoke setters
        self.preview_index = self._preview_index

    def handle_left_btn_clicked(self, widget: Gtk.Widget) -> None:
        self.preview_index_increment(-1)

    def handle_right_btn_clicked(self, widget: Gtk.Widget) -> None:
        self.preview_index_increment(1)

    def handle_preview_index_input_changed(self, widget: Gtk.Widget) -> None:
        self.handle_preview_index_changed()

    def preview_index_increment(self, by: int) -> None:
        self.preview_index = (self.preview_index + by) % self.viewer.props.preview.num_images

    @property
    def preview_index(self) -> int:
        return self.preview_index_input.props.value - 1

    @preview_index.setter
    def preview_index(self, value: int) -> None:
        self.preview_index_input.props.value = value + 1
        self.handle_preview_index_changed()

    def handle_preview_index_changed(self) -> None:
        self.viewer.props.preview.show(self.preview_index)

    @staticmethod
    def can_control(viewer: 'PreviewViewer') -> bool:
        return isinstance(viewer.props.preview, ImageSlideshowObserverPreview)
