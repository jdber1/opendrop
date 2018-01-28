from typing import Iterable

from gi.repository import Gtk
from opendrop.sample_mvp_app.observer_viewer.observer_chooser_dialog.observer_config.local_images.presenter import ImagesConfigIView

from opendrop import observer
from opendrop.sample_mvp_app.observer_viewer.observer_chooser_dialog.observer_config.base_config.view import ObserverConfigView
from opendrop.widgets.file_chooser_button import FileChooserButton
from opendrop.widgets.integer_entry import IntegerEntry


# TODO: if user tries to submit with a blank frame interval or no images selected, show some kind of error/warning.
# also, frame interval needs to be larger than 1
class ImagesConfigView(ObserverConfigView, ImagesConfigIView):
    OBSERVER_TYPE = observer.types.IMAGE_SLIDESHOW

    def setup(self) -> None:
        grid = Gtk.Grid(column_spacing=10, row_spacing=10)
        self.container.pack_start(grid, expand=True, fill=True, padding=0)

        file_input_lbl = Gtk.Label('Images:')
        grid.attach(file_input_lbl, 0, 0, 1, 1)

        file_input_filter = Gtk.FileFilter()

        file_input_filter.add_mime_type('image/png')
        file_input_filter.add_mime_type('image/jpg')

        self.file_input = FileChooserButton(label='Select images', file_filter=file_input_filter,
                                            select_multiple=True)  # type: FileChooserButton
        self.file_input.connect('changed', self._on_file_input_changed)

        grid.attach(self.file_input, 1, 0, 1, 1)



        frame_interval_input_lbl = Gtk.Label('Frame Interval:')
        grid.attach(frame_interval_input_lbl, 0, 1, 1, 1)

        self.frame_interval_input = IntegerEntry()  # type: IntegerEntry

        self.frame_interval_input.connect('changed', self._on_frame_interval_input_changed)

        grid.attach(self.frame_interval_input, 1, 1, 1, 1)

        grid.show_all()

    def _on_file_input_changed(self, widget: FileChooserButton) -> None:
        self.events.on_file_input_changed.fire(widget.filenames)

    def _on_frame_interval_input_changed(self, widget: IntegerEntry) -> None:
        self.events.on_frame_interval_input_changed.fire(int(widget.props.text) if widget.props.text else None)

    def set_file_input(self, filenames: Iterable[str]) -> None:
        self.file_input.filenames = filenames

    def set_frame_interval_input(self, interval: int) -> None:
        self.frame_interval_input.props.text = str(interval)
