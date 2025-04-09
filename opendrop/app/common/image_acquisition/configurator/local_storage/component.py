# Copyright © 2020, Joseph Berry, Rico Tabor (opendrop.dev@gmail.com)
# OpenDrop is released under the GNU GPL License. You are free to
# modify and distribute the code, but always under the same license
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


from gi.repository import Gtk, Gdk, GObject

from opendrop.app.common.services.acquisition import LocalStorageAcquirer
from opendrop.mvp import ComponentSymbol, Presenter, View
from opendrop.utility.bindable.gextension import GObjectPropertyBindable
from opendrop.widgets.file_chooser_button import FileChooserButton
from opendrop.widgets.float_entry import FloatEntry

local_storage_cs = ComponentSymbol()  # type: ComponentSymbol[Gtk.Widget]


@local_storage_cs.view()
class LocalStorageView(View['LocalStoragePresenter', Gtk.Widget]):
    STYLE = '''
    .small-pad {
         min-height: 0px;
         min-width: 0px;
         padding: 6px 4px 6px 4px;
    }

    .error {
        color: red;
        border: 1px solid red;
    }

    .error-text {
        color: red;
    }
    '''

    _STYLE_PROV = Gtk.CssProvider()
    _STYLE_PROV.load_from_data(bytes(STYLE, 'utf-8'))
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), _STYLE_PROV, Gtk.STYLE_PROVIDER_PRIORITY_USER)

    _FILE_INPUT_FILTER = Gtk.FileFilter()

    # OpenCV supported image types
    _FILE_INPUT_FILTER.add_mime_type('image/bmp')
    _FILE_INPUT_FILTER.add_mime_type('image/png')
    _FILE_INPUT_FILTER.add_mime_type('image/jpeg')
    _FILE_INPUT_FILTER.add_mime_type('image/jp2')
    _FILE_INPUT_FILTER.add_mime_type('image/tiff')
    _FILE_INPUT_FILTER.add_mime_type('image/webp')
    _FILE_INPUT_FILTER.add_mime_type('image/x‑portable‑anymap')
    _FILE_INPUT_FILTER.add_mime_type('image/vnd.radiance')

    def _do_init(self) -> Gtk.Widget:
        self._widget = Gtk.Grid(row_spacing=10, column_spacing=10)

        file_chooser_lbl = Gtk.Label('Image files:', xalign=0)
        self._widget.attach(file_chooser_lbl, 0, 0, 1, 1)

        self._file_chooser_inp = FileChooserButton(
            file_filter=self._FILE_INPUT_FILTER,
            select_multiple=True
        )
        self._file_chooser_inp.get_style_context().add_class('small-pad')
        self._widget.attach_next_to(self._file_chooser_inp, file_chooser_lbl, Gtk.PositionType.RIGHT, 1, 1)

        frame_interval_lbl = Gtk.Label('Frame interval (s):')
        self._widget.attach(frame_interval_lbl, 0, 1, 1, 1)

        frame_interval_inp_container = Gtk.Grid()
        self._widget.attach_next_to(frame_interval_inp_container, frame_interval_lbl, Gtk.PositionType.RIGHT, 1, 1)

        self._frame_interval_inp = FloatEntry(lower=0, width_chars=6, invisible_char='\0', caps_lock_warning=False)
        self._frame_interval_inp.get_style_context().add_class('small-pad')
        frame_interval_inp_container.add(self._frame_interval_inp)

        # Error message labels

        self._file_chooser_err_msg_lbl = Gtk.Label(xalign=0)
        self._file_chooser_err_msg_lbl.get_style_context().add_class('error-text')
        self._widget.attach_next_to(self._file_chooser_err_msg_lbl, self._file_chooser_inp, Gtk.PositionType.RIGHT, 1, 1)

        self._frame_interval_err_msg_lbl = Gtk.Label(xalign=0)
        self._frame_interval_err_msg_lbl.get_style_context().add_class('error-text')
        self._widget.attach_next_to(self._frame_interval_err_msg_lbl, frame_interval_inp_container, Gtk.PositionType.RIGHT, 1, 1)

        self._widget.show_all()

        self._frame_interval_inp.bind_property(
            'sensitive',
            self._frame_interval_inp,
            'visibility',
            GObject.BindingFlags.SYNC_CREATE
        )

        self.bn_selected_image_paths = GObjectPropertyBindable(self._file_chooser_inp, 'file-paths')
        self.bn_frame_interval = GObjectPropertyBindable(self._frame_interval_inp, 'value')
        self.bn_frame_interval_sensitive = GObjectPropertyBindable(self._frame_interval_inp, 'sensitive')

        # Set which widget is first focused
        self._file_chooser_inp.grab_focus()

        self.presenter.view_ready()

        return self._widget

    def _do_destroy(self) -> None:
        self._widget.destroy()


@local_storage_cs.presenter(options=['acquirer'])
class LocalStoragePresenter(Presenter['LocalStorageView']):
    def _do_init(self, acquirer: LocalStorageAcquirer) -> None:
        self._acquirer = acquirer

        self.__data_bindings = []
        self.__event_connections = []

    def view_ready(self) -> None:
        self.__data_bindings.extend([
            self._acquirer.bn_frame_interval.bind(
                self.view.bn_frame_interval
            )
        ])

        self.__event_connections.extend([
            self._acquirer.bn_last_loaded_paths.on_changed.connect(self._hdl_model_last_loaded_paths_changed),
            self.view.bn_selected_image_paths.on_changed.connect(self._hdl_view_selected_image_paths_changed)
        ])

        self._hdl_model_last_loaded_paths_changed()

    def _hdl_model_last_loaded_paths_changed(self) -> None:
        if len(self._acquirer.bn_images.get()) == 1:
            self.view.bn_frame_interval_sensitive.set(False)
        else:
            self.view.bn_frame_interval_sensitive.set(True)

        last_loaded_paths = self._acquirer.bn_last_loaded_paths.get()
        selected_image_paths = self.view.bn_selected_image_paths.get()

        if set(last_loaded_paths) != set(selected_image_paths):
            self.view.bn_selected_image_paths.set(last_loaded_paths)

    def _hdl_view_selected_image_paths_changed(self) -> None:
        last_loaded_paths = self._acquirer.bn_last_loaded_paths.get()
        selected_image_paths = self.view.bn_selected_image_paths.get()

        if set(last_loaded_paths) == set(selected_image_paths):
            return

        self._acquirer.load_image_paths(selected_image_paths)

    def _do_destroy(self) -> None:
        for db in self.__data_bindings:
            db.unbind()

        for ec in self.__event_connections:
            ec.disconnect()
