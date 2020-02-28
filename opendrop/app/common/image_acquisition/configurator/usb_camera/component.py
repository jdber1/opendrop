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
#E. Huang, T. Denning, A. Skoufis, J. Qi, R. R. Dagastine, R. F. Tabor
#and J. D. Berry, OpenDrop: Open-source software for pendant drop
#tensiometry & contact angle measurements, submitted to the Journal of
# Open Source Software
#
#These citations help us not only to understand who is using and
#developing OpenDrop, and for what purpose, but also to justify
#continued development of this code and other open source resources.
#
# OpenDrop is distributed WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.  You
# should have received a copy of the GNU General Public License along
# with this software.  If not, see <https://www.gnu.org/licenses/>.
from typing import Optional, Callable, Any

from gi.repository import Gtk, Gdk, GObject

from opendrop.app.common.image_acquirer import USBCameraAcquirer
from opendrop.mvp import ComponentSymbol, Presenter, View
from opendrop.utility.bindable.typing import Bindable
from opendrop.utility.bindable.gextension import GObjectPropertyBindable
from opendrop.widgets.float_entry import FloatEntry
from opendrop.widgets.integer_entry import IntegerEntry

usb_camera_cs = ComponentSymbol()  # type: ComponentSymbol[Gtk.Widget]


@usb_camera_cs.view()
class USBCameraView(View['USBCameraPresenter', Gtk.Widget]):
    STYLE = '''
    .change-cam-dialog-view-footer {
         background-color: gainsboro;
    }

    .small-pad {
         min-height: 0px;
         min-width: 0px;
         padding: 6px 4px 6px 4px;
    }

    .dialog-footer-button {
         min-height: 0px;
         min-width: 0px;
         padding: 8px 6px 8px 6px;
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

    def _do_init(self) -> Gtk.Widget:
        self._change_camera_dialog_cid = None  # type: Any

        self._widget = Gtk.Grid(row_spacing=10, column_spacing=10)

        # Populate self.widget

        camera_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self._widget.attach(camera_container, 0, 0, 2, 1)

        camera_lbl = Gtk.Label('Camera:', xalign=0)
        camera_container.add(camera_lbl)

        self._current_camera_lbl = Gtk.Label(xalign=0)
        camera_container.add(self._current_camera_lbl)

        self._change_camera_btn = Gtk.Button('Connect camera')
        self._change_camera_btn.get_style_context().add_class('small-pad')
        camera_container.add(self._change_camera_btn)

        num_frames_lbl = Gtk.Label('Number of images to capture:', xalign=0)
        self._widget.attach(num_frames_lbl, 0, 1, 1, 1)

        num_frames_inp_container = Gtk.Grid()
        self._widget.attach_next_to(num_frames_inp_container, num_frames_lbl, Gtk.PositionType.RIGHT, 1, 1)

        self._num_frames_inp = IntegerEntry(lower=1, upper=200, value=1, width_chars=6)
        self._num_frames_inp.get_style_context().add_class('small-pad')
        num_frames_inp_container.add(self._num_frames_inp)

        frame_interval_lbl = Gtk.Label('Frame interval (s):', xalign=0)
        self._widget.attach(frame_interval_lbl, 0, 2, 1, 1)

        frame_interval_inp_container = Gtk.Grid()
        self._widget.attach_next_to(frame_interval_inp_container, frame_interval_lbl, Gtk.PositionType.RIGHT, 1, 1)

        self._frame_interval_inp = FloatEntry(lower=0, width_chars=6, sensitive=False, invisible_char='\0')
        self._frame_interval_inp.get_style_context().add_class('small-pad')
        frame_interval_inp_container.add(self._frame_interval_inp)

        self._current_camera_err_msg_lbl = Gtk.Label(xalign=0)
        self._current_camera_err_msg_lbl.get_style_context().add_class('error-text')
        self._widget.attach_next_to(self._current_camera_err_msg_lbl, camera_container, Gtk.PositionType.RIGHT, 1, 1)

        self._num_frames_err_msg_lbl = Gtk.Label(xalign=0)
        self._num_frames_err_msg_lbl.get_style_context().add_class('error-text')
        self._widget.attach_next_to(self._num_frames_err_msg_lbl, num_frames_inp_container, Gtk.PositionType.RIGHT, 1, 1)

        self._frame_interval_err_msg_lbl = Gtk.Label(xalign=0)
        self._frame_interval_err_msg_lbl.get_style_context().add_class('error-text')
        self._widget.attach_next_to(self._frame_interval_err_msg_lbl, frame_interval_inp_container, Gtk.PositionType.RIGHT, 1, 1)

        self._widget.show_all()

        # Wiring things up

        self._change_camera_btn.connect('clicked', lambda *_: self.presenter.hdl_change_camera_btn_clicked())

        self.bn_frame_interval = GObjectPropertyBindable(self._frame_interval_inp, 'value')
        self.bn_num_frames = GObjectPropertyBindable(self._num_frames_inp, 'value')

        self.bn_frame_interval_sensitive = GObjectPropertyBindable(self._frame_interval_inp, 'sensitive')

        self._frame_interval_inp.bind_property(
            'sensitive',
            self._frame_interval_inp,
            'visibility',
            GObject.BindingFlags.SYNC_CREATE
        )

        self.presenter.view_ready()

        return self._widget

    def set_camera_index(self, camera_index: Optional[int]) -> None:
        if camera_index is None:
            self._current_camera_lbl.props.label = ''
            self._current_camera_lbl.props.visible = False
            self._change_camera_btn.props.label = 'Connect camera'
        else:
            self._current_camera_lbl.props.label = '(Connected to index {})'.format(camera_index)
            self._current_camera_lbl.props.visible = True
            self._change_camera_btn.props.label = 'Change camera'

    def show_change_camera_dialog(self) -> None:
        if self._change_camera_dialog_cid is not None:
            return

        self._change_camera_dialog_cid, _ = self.new_component(
            _change_camera_dialog_cs.factory(
                on_response=self.presenter.hdl_change_camera_dialog_response,
                parent_window=self._get_window(),
            )
        )

    def hide_change_camera_dialog(self) -> None:
        if self._change_camera_dialog_cid is None:
            return

        self.remove_component(self._change_camera_dialog_cid)
        self._change_camera_dialog_cid = None

    def _get_window(self) -> Optional[Gtk.Window]:
        toplevel = self._widget.get_toplevel()
        if isinstance(toplevel, Gtk.Window):
            return toplevel
        else:
            return None

    def _do_destroy(self) -> None:
        self._widget.destroy()


@usb_camera_cs.presenter(options=['acquirer'])
class USBCameraPresenter(Presenter['USBCameraView']):
    def _do_init(self, acquirer: USBCameraAcquirer) -> None:
        self._acquirer = acquirer
        self.__data_bindings = []
        self.__event_connections = []

    def view_ready(self) -> None:
        self.__data_bindings.extend([
            self._acquirer.bn_num_frames.bind(self.view.bn_num_frames),
            self._acquirer.bn_frame_interval.bind(self.view.bn_frame_interval),
        ])

        self.__event_connections.extend([
            self._acquirer.bn_num_frames.on_changed.connect(self._update_frame_interval_sensitivity),
            self._acquirer.bn_camera_index.on_changed.connect(self._update_camera_index_indicator),
        ])

        self._update_frame_interval_sensitivity()
        self._update_camera_index_indicator()

    def _update_frame_interval_sensitivity(self) -> None:
        if self._acquirer.bn_num_frames.get() == 1:
            self.view.bn_frame_interval_sensitive.set(False)
        else:
            self.view.bn_frame_interval_sensitive.set(True)

    def _update_camera_index_indicator(self) -> None:
        self.view.set_camera_index(self._acquirer.bn_camera_index.get())

    def hdl_change_camera_btn_clicked(self) -> None:
        self.view.show_change_camera_dialog()

    def hdl_change_camera_dialog_response(self, camera_index: Optional[int]) -> Any:
        if camera_index is not None:
            try:
                self._acquirer.open_camera(camera_index)
            except ValueError:
                return True

        self.view.hide_change_camera_dialog()

    def _do_destroy(self) -> None:
        for db in self.__data_bindings:
            db.unbind()

        for ec in self.__event_connections:
            ec.disconnect()


_change_camera_dialog_cs = ComponentSymbol()  # type: ComponentSymbol[Gtk.Window]


@_change_camera_dialog_cs.view(options=['parent_window'])
class _ChangeCameraDialogView(View['_ChangeCameraDialogPresenter', Gtk.Window]):
    def _do_init(self, parent_window: Optional[Gtk.Window]) -> Gtk.Window:
        self._window = Gtk.Window(
            title='Select camera',
            transient_for=parent_window,
            resizable=False,
            modal=True,
            window_position=Gtk.WindowPosition.CENTER,
        )

        body = Gtk.Grid()
        self._window.add(body)

        content = Gtk.Grid(margin=10, column_spacing=10)
        body.attach(content, 0, 0, 1, 1)

        camera_index_lbl = Gtk.Label('Camera index:')
        content.attach(camera_index_lbl, 0, 0, 1, 1)

        camera_index_inp = IntegerEntry(lower=0, upper=99999, max_length=5, width_chars=6)
        camera_index_inp.get_style_context().add_class('small-pad')
        content.attach_next_to(camera_index_inp, camera_index_lbl, Gtk.PositionType.RIGHT, 1, 1)

        # Setting max_width_chars to 0 seems to allow the label to occupy as much space as its parent, allowing
        # line wrapping to work.
        self._error_msg_lbl = Gtk.Label(margin_top=10, max_width_chars=0)
        self._error_msg_lbl.set_line_wrap(True)
        self._error_msg_lbl.get_style_context().add_class('error-text')
        content.attach(self._error_msg_lbl, 0, 1, 2, 1)

        footer = Gtk.Grid()
        footer.get_style_context().add_class('change-cam-dialog-view-footer')
        footer.get_style_context().add_class('linked')
        body.attach(footer, 0, 1, 1, 1)

        cancel_btn = Gtk.Button('Cancel', hexpand=True)
        cancel_btn.get_style_context().add_class('dialog-footer-button')
        footer.attach(cancel_btn, 0, 0, 1, 1)

        connect_btn = Gtk.Button('Connect', hexpand=True)
        connect_btn.get_style_context().add_class('dialog-footer-button')
        footer.attach(connect_btn, 1, 0, 1, 1)

        self._window.show_all()

        # Hide the error message label (since self.widget.show_all() would have made all descendant widgets
        # visible).
        self._error_msg_lbl.hide()

        # Wiring things up

        connect_btn.connect('clicked', lambda *_: self.presenter.connect())
        cancel_btn.connect('clicked', lambda *_: self.presenter.cancel())

        self._window.connect('delete-event', self._hdl_widget_delete_event)

        self.bn_camera_index = GObjectPropertyBindable(camera_index_inp, 'value')  # type: Bindable[int]
        self.bn_connect_btn_sensitive = GObjectPropertyBindable(connect_btn, 'sensitive')  # type: Bindable[bool]

        self.presenter.view_ready()

        return self._window

    def show_camera_connection_fail_message(self, cam_idx: int) -> None:
        self._set_error_msg('Failed to connect to camera index {}.'.format(cam_idx))

    def _set_error_msg(self, text: Optional[str]) -> None:
        if text is None:
            self._error_msg_lbl.props.label = None
            self._error_msg_lbl.props.visible = False
            return

        self._error_msg_lbl.props.label = text
        self._error_msg_lbl.props.visible = True

    def _hdl_widget_delete_event(self, window: Gtk.Window, data: Gdk.Event) -> bool:
        self.presenter.cancel()
        # Return True to prevent the window from closing.
        return True

    def _do_destroy(self) -> None:
        self._window.destroy()


@_change_camera_dialog_cs.presenter(options=['on_response'])
class _ChangeCameraDialogPresenter(Presenter['_ChangeCameraDialogView']):
    def _do_init(self, on_response: Callable[[Optional[int]], Any]) -> None:
        self._on_response = on_response

        self.__event_connections = []

    def view_ready(self) -> None:
        self.__event_connections.extend([
            self.view.bn_camera_index.on_changed.connect(self._update_connect_btn_sensitivity),
        ])
        self._update_connect_btn_sensitivity()

    def connect(self) -> None:
        camera_index = self.view.bn_camera_index.get()
        if camera_index is None:
            return

        failure = self._on_response(camera_index)

        if failure:
            self.view.show_camera_connection_fail_message(camera_index)

    def cancel(self) -> None:
        self._on_response(None)

    def _update_connect_btn_sensitivity(self) -> None:
        cam_idx = self.view.bn_camera_index.get()
        if cam_idx is None:
            self.view.bn_connect_btn_sensitive.set(False)
        else:
            self.view.bn_connect_btn_sensitive.set(True)

    def _do_destroy(self) -> None:
        for ec in self.__event_connections:
            ec.disconnect()
