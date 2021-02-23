# Copyright © 2020, Joseph Berry, Rico Tabor (opendrop.dev@gmail.com)
# OpenDrop is released under the GNU GPL License. You are free to
# modify and distribute the code, but always under the same license
# (i.e. you cannot make commercial derivatives).
#
# If you use this software in your research, please cite the following
# journal articles:
#
# J. D. Berry, M. J. Neeson, R. R. Dagastine, D. Y. C. Chan and
# R. F. Tabor, Measurement of surface and interfacial tension using
# pendant drop tensiometry. Journal of Colloid and Interface Science 454
# (2015) 226–237. https://doi.org/10.1016/j.jcis.2015.05.012
#
# E. Huang, T. Denning, A. Skoufis, J. Qi, R. R. Dagastine, R. F. Tabor
# and J. D. Berry, OpenDrop: Open-source software for pendant drop
# tensiometry & contact angle measurements, submitted to the Journal of
# Open Source Software
#
# These citations help us not only to understand who is using and
# developing OpenDrop, and for what purpose, but also to justify
# continued development of this code and other open source resources.
#
# OpenDrop is distributed WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.  You
# should have received a copy of the GNU General Public License along
# with this software.  If not, see <https://www.gnu.org/licenses/>.


from typing import Tuple, Optional, Iterable

from gi.repository import Gtk, GObject


class FileChooserButton(Gtk.Button):
    def __init__(
            self,
            label: str = 'Choose files',
            dialog_title: str = 'Select files',
            file_filter: Optional[Gtk.FileFilter] = None,
            select_multiple: bool = False,
            *args,
            **kwargs
    ):
        super().__init__(label=label, *args, **kwargs)

        self._no_files_label = label
        self._file_paths: Tuple[str] = tuple()

        self.dialog_title = dialog_title
        self.file_filter = file_filter
        self.select_multiple = select_multiple

        self._active_dialog: Optional[Gtk.FileChooserNative] = None

    def do_clicked(self) -> None:
        if self._active_dialog is not None:
            return

        self._active_dialog = Gtk.FileChooserNative.new(
            title=self.dialog_title,
            parent=self.get_toplevel(),
            action=Gtk.FileChooserAction.OPEN,
            accept_label='Open',
            cancel_label='Cancel',
        )

        self._active_dialog.props.modal = True
        self._active_dialog.props.select_multiple = True
        self._active_dialog.props.filter = self.file_filter

        def hdl_file_chooser_dialog_response(dialog: Gtk.FileChooserDialog, response: Gtk.ResponseType):
            if response == Gtk.ResponseType.ACCEPT:
                self.file_paths = dialog.get_filenames()

            # Other possible responses are:
            #     Gtk.ResponseType.DELETE_EVENT
            #     Gtk.ResponseType.CLOSE

            dialog.destroy()
            self._active_dialog = None

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
