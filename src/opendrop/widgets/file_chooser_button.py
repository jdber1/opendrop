from typing import List, Tuple, Optional, Iterable

from gi.repository import Gtk, GObject


class FileChooserButton(Gtk.Button):
    def __init__(self, label: str = 'Choose files', dialog_title: str = 'Select files',
                 file_filter: Optional[Gtk.FileFilter] = None, select_multiple: bool = False):
        super().__init__(label=label)

        self._filenames = tuple()  # type: Tuple[str]

        self.dialog_title = dialog_title  # type: str
        self.file_filter = file_filter  # type: Optional[Gtk.FileFilter]
        self.select_multiple = select_multiple # type: bool

        self.connect('clicked', self.handle_clicked)

    def handle_clicked(self, _) -> None:
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

        file_chooser_dialog.show()

        def handle_file_chooser_dialog_response(dialog: Gtk.FileChooserDialog, response: Gtk.ResponseType):
            if response == Gtk.ResponseType.ACCEPT:
                self.filenames = file_chooser_dialog.get_filenames()

            # Other possible responses are:
            #     Gtk.ResponseType.DELETE_EVENT
            #     Gtk.ResponseType.CLOSE

            dialog.destroy()

        file_chooser_dialog.connect('response', handle_file_chooser_dialog_response)

    @property
    def filenames(self) -> Tuple[str]:
        return self._filenames

    @filenames.setter
    def filenames(self, value: Iterable[str]) -> None:
        self._filenames = tuple(value)

        if len(value) == 1:
            self.props.label = 'File selected'
        else:
            self.props.label = '{} files selected'.format(len(value))

        self.emit('changed')

    @property
    def filename(self) -> Optional[str]:
        return self._filenames[0] if self._filenames else None

    @filename.setter
    def filename(self, value: str) -> None:
        self._filenames = (value,)


GObject.signal_new(
    'changed', FileChooserButton, GObject.SIGNAL_RUN_LAST, GObject.TYPE_PYOBJECT, ()
)
