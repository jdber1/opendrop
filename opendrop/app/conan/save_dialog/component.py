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


from pathlib import Path
from typing import Optional, Callable, Any

from gi.repository import Gtk, Gdk

from opendrop.app.common.analysis_saver.figure_options import figure_options_cs
from opendrop.mvp import ComponentSymbol, View, Presenter
from opendrop.utility.bindable import AccessorBindable
from opendrop.utility.bindable.gextension import GObjectPropertyBindable
from opendrop.widgets.error_dialog import ErrorDialog
from opendrop.widgets.yes_no_dialog import YesNoDialog
from opendrop.app.conan.services.save import ConanSaveParamsFactory

conan_save_dialog_cs = ComponentSymbol()  # type: ComponentSymbol[Gtk.Window]


@conan_save_dialog_cs.view(options=['parent_window'])
class ConanSaveDialogView(View['ConanSaveDialogPresenter', Gtk.Window]):
    STYLE = '''
    .small-pad {
         min-height: 0px;
         min-width: 0px;
         padding: 6px 4px 6px 4px;
    }

    .small-combobox .combo {
        min-height: 0px;
        min-width: 0px;
    }

    .conan-analysis-saver-view-footer-button {
        min-height: 0px;
        min-width: 60px;
        padding: 10px 4px 10px 4px;
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

    def _do_init(self, parent_window: Optional[Gtk.Window] = None) -> Gtk.Window:
        self._window = Gtk.Window(
            title='Save analysis',
            resizable=False,
            modal=True,
            transient_for=parent_window,
            window_position=Gtk.WindowPosition.CENTER,
        )

        body = Gtk.Grid(margin=10, row_spacing=10)
        self._window.add(body)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        body.attach(content, 0, 0, 1, 1)

        save_location_frame = Gtk.Frame(label='Save location')
        content.add(save_location_frame)
        save_location_content = Gtk.Grid(margin=10, column_spacing=10, row_spacing=5)
        save_location_frame.add(save_location_content)

        save_dir_lbl = Gtk.Label('Parent:', xalign=0)
        save_location_content.attach(save_dir_lbl, 0, 0, 1, 1)

        self._save_dir_parent_inp = Gtk.FileChooserButton(action=Gtk.FileChooserAction.SELECT_FOLDER, hexpand=True)
        self._save_dir_parent_inp.get_style_context().add_class('small-combobox')
        save_location_content.attach_next_to(self._save_dir_parent_inp, save_dir_lbl, Gtk.PositionType.RIGHT, 1, 1)

        save_dir_parent_err_lbl = Gtk.Label(xalign=0, width_request=190)
        save_dir_parent_err_lbl.get_style_context().add_class('error-text')
        save_location_content.attach_next_to(save_dir_parent_err_lbl, self._save_dir_parent_inp, Gtk.PositionType.RIGHT, 1, 1)

        save_name_lbl = Gtk.Label('Name:', xalign=0)
        save_location_content.attach(save_name_lbl, 0, 1, 1, 1)

        save_dir_name_inp = Gtk.Entry()
        save_dir_name_inp.get_style_context().add_class('small-pad')
        save_location_content.attach_next_to(save_dir_name_inp, save_name_lbl, Gtk.PositionType.RIGHT, 1, 1)

        save_dir_name_err_lbl = Gtk.Label(xalign=0, width_request=190)
        save_dir_name_err_lbl.get_style_context().add_class('error-text')
        save_location_content.attach_next_to(save_dir_name_err_lbl, save_dir_name_inp, Gtk.PositionType.RIGHT, 1, 1)

        figures_frame = Gtk.Frame(label='Figures')
        content.add(figures_frame)
        figures_content = Gtk.Grid(margin=10, column_spacing=10, row_spacing=5)
        figures_frame.add(figures_content)

        _, angles_figure_options_area = self.new_component(
            figure_options_cs.factory(
                model=self.presenter.angle_figure_options,
                figure_name='contact angles plot',
            )
        )
        angles_figure_options_area.show()
        figures_content.attach(angles_figure_options_area, 0, 0, 1, 1)

        footer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        body.attach_next_to(footer, content, Gtk.PositionType.BOTTOM, 1, 1)

        ok_btn = Gtk.Button('OK')
        ok_btn.get_style_context().add_class('conan-analysis-saver-view-footer-button')
        footer.pack_end(ok_btn, expand=False, fill=False, padding=0)

        cancel_btn = Gtk.Button('Cancel')
        cancel_btn.get_style_context().add_class('conan-analysis-saver-view-footer-button')
        footer.pack_end(cancel_btn, expand=False, fill=False, padding=0)

        self._window.show_all()

        # Wiring things up

        ok_btn.connect('clicked', lambda *_: self.presenter.ok())
        cancel_btn.connect('clicked', lambda *_: self.presenter.cancel())

        self._window.connect('delete-event', self._hdl_window_delete_event)

        self.bn_save_dir_parent = AccessorBindable(self._get_save_dir_parent, self._set_save_dir_parent)
        self.bn_save_dir_name = GObjectPropertyBindable(save_dir_name_inp, 'text')

        self._confirm_overwrite_dialog = None
        self._file_exists_info_dialog = None

        self.presenter.view_ready()

        return self._window

    def _hdl_window_delete_event(self, widget: Gtk.Dialog, event: Gdk.Event) -> bool:
        self.presenter.cancel()

        # return True to prevent the dialog from closing.
        return True

    def show_confirm_overwrite_dialog(self, path: Path) -> None:
        if self._confirm_overwrite_dialog is not None:
            return

        self._confirm_overwrite_dialog = YesNoDialog(
            message_format=(
                "This save location '{!s}' already exists, do you want to clear its contents?"
                .format(path)
            ),
            parent=self._window
        )

        self._confirm_overwrite_dialog.connect('response', self._hdl_confirm_overwrite_dialog_response)
        self._confirm_overwrite_dialog.connect('delete-event', lambda *_: True)

        self._confirm_overwrite_dialog.show()

    def _hdl_confirm_overwrite_dialog_response(self, widget: Gtk.Dialog, response: Gtk.ResponseType) -> None:
        accept = (response == Gtk.ResponseType.YES)
        self.presenter.hdl_confirm_overwrite_dialog_response(accept)

    def hide_confirm_overwrite_dialog(self) -> None:
        if self._confirm_overwrite_dialog is None:
            return

        self._confirm_overwrite_dialog.destroy()
        self._confirm_overwrite_dialog = None

    def tell_user_file_exists_and_is_not_a_directory(self, path: Path) -> None:
        if self._file_exists_info_dialog is not None:
            return

        self._file_exists_info_dialog = ErrorDialog(
            message_format=(
                "Cannot save to '{!s}', the path already exists and is a non-directory file."
                .format(path)
            ),
            parent=self._window
        )
        self._file_exists_info_dialog.show()

        def hdl_delete_event(*_) -> None:
            self._file_exists_info_dialog = None

        def hdl_response(dialog: Gtk.Window, *_) -> None:
            self._file_exists_info_dialog = None
            dialog.destroy()

        self._file_exists_info_dialog.connect('delete-event', hdl_delete_event)
        self._file_exists_info_dialog.connect('response', hdl_response)

    def _get_save_dir_parent(self) -> Path:
        path_str = self._save_dir_parent_inp.get_filename()
        path = Path(path_str) if path_str is not None else None
        return path

    def _set_save_dir_parent(self, path: Optional[Path]) -> None:
        if path is None:
            self._save_dir_parent_inp.unselect_all()
            return

        path = str(path)
        self._save_dir_parent_inp.set_filename(path)

    def flush_save_dir_parent(self) -> None:
        self.bn_save_dir_parent.poke()

    def _do_destroy(self) -> None:
        self._window.destroy()
        self.hide_confirm_overwrite_dialog()


@conan_save_dialog_cs.presenter(options=['model', 'do_ok', 'do_cancel'])
class ConanSaveDialogPresenter(Presenter['ConanSaveDialogView']):
    def _do_init(
            self,
            model: ConanSaveParamsFactory,
            do_ok: Callable[[], Any],
            do_cancel: Callable[[], Any],
    ) -> None:
        self._model = model

        self._do_ok = do_ok
        self._do_cancel = do_cancel

        self.angle_figure_options = model.angle_figure_opts

        self.__data_bindings = []

    def view_ready(self) -> None:
        self.__data_bindings.extend([
            self._model.bn_save_dir_parent.bind(
                self.view.bn_save_dir_parent
            ),
            self._model.bn_save_dir_name.bind(
                self.view.bn_save_dir_name
            ),
        ])

    def ok(self, confirm_overwrite: bool = False) -> None:
        self.view.flush_save_dir_parent()

        save_root_dir = self._model.save_root_dir
        if save_root_dir.exists():
            # Specified save path already exists

            if (
                    save_root_dir.is_dir() and
                    len(tuple(save_root_dir.iterdir())) > 0 and
                    not confirm_overwrite
            ):
                self.view.show_confirm_overwrite_dialog(save_root_dir)
                return
            elif not save_root_dir.is_dir():
                # Path exists, but is not a directory. We will not attempt to remove whatever it is.
                self.view.tell_user_file_exists_and_is_not_a_directory(save_root_dir)
                return
            else:
                # Ok to overwrite
                pass

        self._do_ok()

    def hdl_confirm_overwrite_dialog_response(self, accept: bool) -> None:
        self.view.hide_confirm_overwrite_dialog()

        if accept:
            self.ok(confirm_overwrite=True)

    def cancel(self) -> None:
        self._do_cancel()

    def _do_destroy(self) -> None:
        for db in self.__data_bindings:
            db.unbind()
