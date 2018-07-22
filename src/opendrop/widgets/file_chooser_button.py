from typing import Tuple, Optional, Iterable

from gi.repository import Gtk, GObject


class FileChooserButton(Gtk.Button):
    def __init__(self, label: str = 'Choose files', dialog_title: str = 'Select files',
                 file_filter: Optional[Gtk.FileFilter] = None, select_multiple: bool = False, *args, **kwargs):
        super().__init__(label=label, *args, **kwargs)

        self._no_files_label = label
        self._file_paths = tuple()  # type: Tuple[str]

        self.dialog_title = dialog_title
        self.file_filter = file_filter
        self.select_multiple = select_multiple

        self._active_dialog = None  # type: Optional[Gtk.FileChooserDialog]

    def do_clicked(self) -> None:
        if self._active_dialog is not None:
            return

        self._active_dialog = Gtk.FileChooserDialog(
            title=self.dialog_title,
            parent=self.get_toplevel(),
            modal=True,
            action=Gtk.FileChooserAction.OPEN,
            select_multiple=self.select_multiple,
            filter=self.file_filter,
            buttons=(
                'Cancel', Gtk.ResponseType.CANCEL,
                'Open', Gtk.ResponseType.ACCEPT
            ),
        )

        self._active_dialog.connect('destroy', lambda *_: setattr(self, '_active_dialog', None))

        def hdl_file_chooser_dialog_response(dialog: Gtk.FileChooserDialog, response: Gtk.ResponseType):
            if response == Gtk.ResponseType.ACCEPT:
                self.file_paths = dialog.get_filenames()

            # Other possible responses are:
            #     Gtk.ResponseType.DELETE_EVENT
            #     Gtk.ResponseType.CLOSE

            dialog.destroy()

        self._active_dialog.connect('response', hdl_file_chooser_dialog_response)
        self._active_dialog.show()

    @GObject.Property
    def file_paths(self) -> Tuple[str]:
        return self._file_paths

    @file_paths.setter
    def file_paths(self, value: Iterable[str]) -> None:
        self._file_paths = tuple(value)

        value_len = len(self._file_paths)

        if value_len == 0:
            self.props.label = self._no_files_label
        elif value_len == 1:
            self.props.label = 'File selected'
        else:
            self.props.label = '{} files selected'.format(value_len)

    get_file_paths = file_paths.fget
    set_file_paths = file_paths.fset
