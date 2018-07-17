from typing import Tuple, Optional, Iterable

from gi.repository import Gtk, GObject


class FileChooserButton(Gtk.Button):
    def __init__(self, label: str = 'Choose files', dialog_title: str = 'Select files',
                 file_filter: Optional[Gtk.FileFilter] = None, select_multiple: bool = False):
        super().__init__(label=label)

        self._no_files_label = label
        self._file_paths = tuple()  # type: Tuple[str]

        self.dialog_title = dialog_title
        self.file_filter = file_filter
        self.select_multiple = select_multiple

        self._dialog_open = False

    def do_clicked(self) -> None:
        if self._dialog_open:
            return

        self._dialog_open = True

        file_chooser_dialog = Gtk.FileChooserDialog(
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

        def set_dialog_open_to_false(*_):
            self._dialog_open = False

        file_chooser_dialog.connect('destroy', set_dialog_open_to_false)
        file_chooser_dialog.show()

        def hdl_file_chooser_dialog_response(dialog: Gtk.FileChooserDialog, response: Gtk.ResponseType):
            if response == Gtk.ResponseType.ACCEPT:
                self.file_paths = file_chooser_dialog.get_filenames()

            # Other possible responses are:
            #     Gtk.ResponseType.DELETE_EVENT
            #     Gtk.ResponseType.CLOSE

            dialog.destroy()

        file_chooser_dialog.connect('response', hdl_file_chooser_dialog_response)

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
