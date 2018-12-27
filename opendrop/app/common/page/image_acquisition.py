from typing import Any, Generic, TypeVar, Callable, Optional, Sequence, MutableSequence, Tuple, Type, MutableMapping

from gi.repository import Gtk, Gdk

from opendrop.app.common.analysis_model.image_acquisition.default_types import DefaultImageAcquisitionImplType, \
    LocalImagesImageAcquisitionImpl, USBCameraImageAcquisitionImpl
from opendrop.app.common.analysis_model.image_acquisition.image_acquisition import ImageAcquisition, \
    ImageAcquisitionImpl, ImageAcquisitionImplType
from opendrop.component.gtk_widget_view import GtkWidgetView
from opendrop.component.stack import StackModel
from opendrop.mytypes import Destroyable
from opendrop.utility.bindable.bindable import AtomicBindableVar, AtomicBindableAdapter, AtomicBindable
from opendrop.utility.bindable.binding import Binding, AtomicBindingMITM
from opendrop.utility.bindablegext.bindable import link_atomic_bn_adapter_to_g_prop
from opendrop.utility.events import Event
from opendrop.utility.speaker import Speaker
from opendrop.widgets.file_chooser_button import FileChooserButton
from opendrop.widgets.float_entry import FloatEntry
from opendrop.widgets.integer_entry import IntegerEntry

# Dependency injection configuration stuff.

_impl_type_to_config_view_factory = {}  # type: MutableMapping[ImageAcquisitionImplType, Callable[[], GtkWidgetView]]
_presenter_factory_for_what_model_and_view = []  # type: MutableSequence[Tuple[Callable[[ImageAcquisitionImpl, Any], Destroyable], Type[ImageAcquisitionImpl], Type]]


T = TypeVar('T', bound=Callable[[], GtkWidgetView])
def this_config_view_is_for_impl_type(impl_type: ImageAcquisitionImplType) -> Callable[[T], T]:
    def actual(view_factory: T) -> T:
        _impl_type_to_config_view_factory[impl_type] = view_factory
        return view_factory
    return actual


U = TypeVar('U', bound=Callable[[], Destroyable])
def this_presenter_attaches_to(impl_cls: Type[ImageAcquisitionImpl], view_cls: Type) -> Callable[[U], U]:
    def actual(presenter_factory: U) -> U:
        _presenter_factory_for_what_model_and_view.append((presenter_factory, impl_cls, view_cls))
        return presenter_factory
    return actual


def create_view_for_impl_type(impl_type: ImageAcquisitionImplType) -> GtkWidgetView:
    try:
        return _impl_type_to_config_view_factory[impl_type]()
    except KeyError:
        raise ValueError('Failed to create configuration view for impl. type `{}`'.format(typ))


def create_presenter_for_impl_and_view(impl: ImageAcquisitionImpl, view: Any) -> Destroyable:
    for candidate_presenter_factory, supports_impl_cls, supports_view_cls in _presenter_factory_for_what_model_and_view:
        if isinstance(impl, supports_impl_cls) and isinstance(view, supports_view_cls):
            return candidate_presenter_factory(impl, view)
    else:
        raise ValueError('Failed to create a presenter for impl. `{}` and view `{}`'.format(impl, view))


# Main classes starts here.

# View and presenter for 'Local Images'

@this_config_view_is_for_impl_type(DefaultImageAcquisitionImplType.LOCAL_IMAGES)
class LocalImagesImageAcquisitionImplView(GtkWidgetView[Gtk.Grid]):
    FILE_INPUT_FILTER = Gtk.FileFilter()
    FILE_INPUT_FILTER.add_mime_type('image/png')
    FILE_INPUT_FILTER.add_mime_type('image/jpg')

    STYLE = '''
    .small-pad {
         min-height: 0px;
         min-width: 0px;
         padding: 6px 4px 6px 4px;
    }
    '''

    _STYLE_PROV = Gtk.CssProvider()
    _STYLE_PROV.load_from_data(bytes(STYLE, 'utf-8'))
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), _STYLE_PROV, Gtk.STYLE_PROVIDER_PRIORITY_USER)

    def __init__(self) -> None:
        self.widget = Gtk.Grid(row_spacing=10, column_spacing=10)

        file_chooser_lbl = Gtk.Label('Image files:', xalign=0)
        self.widget.attach(file_chooser_lbl, 0, 0, 1, 1)

        self._file_chooser_inp = FileChooserButton(file_filter=LocalImagesImageAcquisitionImplView.FILE_INPUT_FILTER,
                                                   select_multiple=True)
        self._file_chooser_inp.get_style_context().add_class('small-pad')
        self.widget.attach_next_to(self._file_chooser_inp, file_chooser_lbl, Gtk.PositionType.RIGHT, 1, 1)

        frame_interval_lbl = Gtk.Label('Frame interval (s):')
        self.widget.attach(frame_interval_lbl, 0, 1, 1, 1)

        frame_interval_inp_container = Gtk.Grid()
        self.widget.attach_next_to(frame_interval_inp_container, frame_interval_lbl, Gtk.PositionType.RIGHT, 1, 1)

        self._frame_interval_inp = FloatEntry(lower=0, width_chars=6)
        self._frame_interval_inp.get_style_context().add_class('small-pad')
        frame_interval_inp_container.add(self._frame_interval_inp)

        self.widget.show_all()

        self.bn_selected_image_paths = AtomicBindableAdapter()
        link_atomic_bn_adapter_to_g_prop(self.bn_selected_image_paths, self._file_chooser_inp, 'file-paths')

        self.bn_frame_interval = AtomicBindableAdapter()
        link_atomic_bn_adapter_to_g_prop(self.bn_frame_interval, self._frame_interval_inp, 'value')


@this_presenter_attaches_to(LocalImagesImageAcquisitionImpl, LocalImagesImageAcquisitionImplView)
class LocalImagesImageAcquisitionImplPresenter(Destroyable):
    def __init__(self, impl: LocalImagesImageAcquisitionImpl, view: LocalImagesImageAcquisitionImplView) -> None:
        self._impl = impl
        self._view = view

        self.__event_connections = [
            self._impl.bn_last_loaded_paths.on_changed.connect(self._hdl_impl_last_loaded_paths_changed,
                                                               immediate=True),
            self._view.bn_selected_image_paths.on_changed.connect(self._hdl_view_user_input_image_paths_changed,
                                                                  immediate=True)
         ]

        self.__data_bindings = [
            Binding(self._impl.bn_frame_interval, self._view.bn_frame_interval)
        ]

        self._hdl_impl_last_loaded_paths_changed()

    def _hdl_impl_last_loaded_paths_changed(self) -> None:
        impl_last_loaded_paths = set(self._impl.bn_last_loaded_paths.get())
        view_selected_image_paths = set(self._view.bn_selected_image_paths.get())

        if impl_last_loaded_paths == view_selected_image_paths:
            return

        self._view.bn_selected_image_paths.set(self._impl.bn_last_loaded_paths.get())

    def _hdl_view_user_input_image_paths_changed(self) -> None:
        new_image_paths = self._view.bn_selected_image_paths.get()

        if set(self._impl.bn_last_loaded_paths.get()) == set(new_image_paths):
            return

        self._impl.load_image_paths(self._view.bn_selected_image_paths.get())

    def destroy(self) -> None:
        for ec in self.__event_connections:
            ec.disconnect()

        for db in self.__data_bindings:
            db.unbind()


# View and presenter for 'USB Camera'

@this_config_view_is_for_impl_type(DefaultImageAcquisitionImplType.USB_CAMERA)
class USBCameraImageAcquisitionImplView(GtkWidgetView[Gtk.Grid]):
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
    
    .error-label {
        color: red;
    }
    '''

    _STYLE_PROV = Gtk.CssProvider()
    _STYLE_PROV.load_from_data(bytes(STYLE, 'utf-8'))
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), _STYLE_PROV, Gtk.STYLE_PROVIDER_PRIORITY_USER)

    class ChangeCameraDialogView(GtkWidgetView[Gtk.Window]):
        def __init__(self, parent_view: 'USBCameraImageAcquisitionImplView') -> None:
            self._parent_view = parent_view
            toplevel_win = self._parent_view.widget.get_toplevel()
            if not isinstance(toplevel_win, Gtk.Window):
                toplevel_win = None

            self.widget = Gtk.Window(resizable=False, transient_for=toplevel_win, modal=True)

            # Populating self.widget

            body = Gtk.Grid()
            self.widget.add(body)

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
            self._error_msg_lbl.get_style_context().add_class('error-label')
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

            self.widget.show_all()

            # Hide the error message label (since self.widget.show_all() would have made all descendant widgets
            # visible).
            self._error_msg_lbl.hide()

            # Wiring things up

            self.on_connect_btn_clicked = Event()
            connect_btn.connect('clicked', lambda *_: self.on_connect_btn_clicked.fire())

            self.on_cancel_btn_clicked = Event()
            cancel_btn.connect('clicked', lambda *_: self.on_cancel_btn_clicked.fire())

            self.on_request_close_window = Event()
            self.widget.connect('delete-event', self._hdl_widget_delete_event)

            self.bn_camera_index = AtomicBindableAdapter()  # type: AtomicBindable[int]
            link_atomic_bn_adapter_to_g_prop(self.bn_camera_index, camera_index_inp, 'value')

            self.bn_camera_inp_text = AtomicBindableAdapter()  # type: AtomicBindable[str]
            link_atomic_bn_adapter_to_g_prop(self.bn_camera_inp_text, camera_index_inp, 'text')

            self.bn_connect_btn_sensitive = AtomicBindableAdapter()
            link_atomic_bn_adapter_to_g_prop(self.bn_connect_btn_sensitive, connect_btn, 'sensitive')

        def show_camera_connection_fail_msg(self, cam_idx: int) -> None:
            self._set_error_msg('Failed to connect to camera index {}.'.format(cam_idx))

        def hide(self) -> None:
            self._parent_view.hide_change_camera_dialog()

        def _set_error_msg(self, text: Optional[str]) -> None:
            if text is None:
                self._error_msg_lbl.props.label = None
                self._error_msg_lbl.props.visible = False
                return

            self._error_msg_lbl.props.label = text
            self._error_msg_lbl.props.visible = True

        def _hdl_widget_delete_event(self, window: Gtk.Window, data: Gdk.Event) -> bool:
            self.on_request_close_window.fire()
            # Return True to prevent the window from closing.
            return True

        def _actual_destroy(self) -> None:
            self.widget.destroy()

    def __init__(self) -> None:
        self.widget = Gtk.Grid(row_spacing=10, column_spacing=10)

        # Populate self.widget

        camera_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.widget.attach(camera_container, 0, 0, 3, 1)

        # Filler element for spacing.
        self.widget.attach(Gtk.Grid(hexpand=True), 2, 1, 1, 1)

        camera_lbl = Gtk.Label('Camera:', xalign=0)
        camera_container.add(camera_lbl)

        self._current_camera_lbl = Gtk.Label(xalign=0)
        camera_container.add(self._current_camera_lbl)

        self._change_camera_btn = Gtk.Button('Connect camera')
        self._change_camera_btn.get_style_context().add_class('small-pad')
        camera_container.add(self._change_camera_btn)

        num_images_lbl = Gtk.Label('Number of images to capture:', xalign=0)
        self.widget.attach(num_images_lbl, 0, 1, 1, 1)

        num_frames_entry_container = Gtk.Grid()
        self.widget.attach_next_to(num_frames_entry_container, num_images_lbl, Gtk.PositionType.RIGHT, 1, 1)

        num_frames_entry = IntegerEntry(lower=0, width_chars=6)
        num_frames_entry.get_style_context().add_class('small-pad')
        num_frames_entry_container.add(num_frames_entry)

        frame_interval_lbl = Gtk.Label('Frame interval (s):', xalign=0)
        self.widget.attach(frame_interval_lbl, 0, 2, 1, 1)

        frame_interval_entry_container = Gtk.Grid()
        self.widget.attach_next_to(frame_interval_entry_container, frame_interval_lbl, Gtk.PositionType.RIGHT, 1, 1)

        frame_interval_entry = FloatEntry(lower=0, width_chars=6)
        frame_interval_entry.get_style_context().add_class('small-pad')
        frame_interval_entry_container.add(frame_interval_entry)

        self.widget.show_all()

        # Wiring things up

        self.on_change_camera_btn_clicked = Event()
        self._change_camera_btn.connect('clicked', lambda *_: self.on_change_camera_btn_clicked.fire())

        self.bn_current_camera_index = AtomicBindableAdapter(setter=self._set_current_camera_index)  # type: AtomicBindable[Optional[int]]
        self.bn_num_frames = AtomicBindableAdapter()
        self.bn_frame_interval = AtomicBindableAdapter()

        link_atomic_bn_adapter_to_g_prop(self.bn_num_frames, num_frames_entry, 'value')
        link_atomic_bn_adapter_to_g_prop(self.bn_frame_interval, frame_interval_entry, 'value')

        self._active_change_camera_dialog_view = None  # type: Optional[USBCameraImageAcquisitionImplView.ChangeCameraDialogView]

    def _set_current_camera_index(self, value: Optional[int]) -> None:
        if value is None:
            self._current_camera_lbl.props.label = ''
            self._current_camera_lbl.props.visible = False
            self._change_camera_btn.props.label = 'Connect camera'
        else:
            self._current_camera_lbl.props.label = '(Connected to index {})'.format(value)
            self._current_camera_lbl.props.visible = True
            self._change_camera_btn.props.label = 'Change camera'

    def show_change_camera_dialog(self) -> 'USBCameraImageAcquisitionImplView.ChangeCameraDialogView':
        if self._active_change_camera_dialog_view is not None:
            # Existing change camera dialog already exists.
            return self._active_change_camera_dialog_view
        self._active_change_camera_dialog_view = USBCameraImageAcquisitionImplView.ChangeCameraDialogView(self)
        return self._active_change_camera_dialog_view

    def hide_change_camera_dialog(self) -> None:
        if self._active_change_camera_dialog_view is None:
            # No change camera dialog exists, ignore.
            return
        self._active_change_camera_dialog_view._actual_destroy()
        self._active_change_camera_dialog_view = None


@this_presenter_attaches_to(USBCameraImageAcquisitionImpl, USBCameraImageAcquisitionImplView)
class USBCameraImageAcquisitionImplPresenter:
    class ChangeCameraDialogPresenter:
        def __init__(self, parent: 'USBCameraImageAcquisitionImplPresenter', impl: USBCameraImageAcquisitionImpl,
                     view: USBCameraImageAcquisitionImplView.ChangeCameraDialogView) -> None:
            self._parent = parent
            self._impl = impl
            self._view = view

            self.tick = False

            self.__event_connections = [
                self._view.on_connect_btn_clicked.connect(self._hdl_view_on_connect_btn_clicked, immediate=True),
                self._view.on_cancel_btn_clicked.connect(self._destroy_and_hide_dialog, immediate=True),
                self._view.on_request_close_window.connect(self._destroy_and_hide_dialog, immediate=True),
                self._view.bn_camera_inp_text.on_changed.connect(self._hdl_view_camera_inp_text_changed, immediate=True)
            ]

            self._hdl_view_camera_inp_text_changed()

        def _hdl_view_on_connect_btn_clicked(self) -> None:
            cam_idx = self._view.bn_camera_index.get()

            if cam_idx is None:
                return

            try:
                self._impl.open_camera(cam_idx)
                self._destroy_and_hide_dialog()
            except ValueError:
                self._view.show_camera_connection_fail_msg(cam_idx)

        def _hdl_view_camera_inp_text_changed(self) -> None:
            cam_idx = self._view.bn_camera_index.get()
            if cam_idx is None:
                self._view.bn_connect_btn_sensitive.set(False)
            else:
                self._view.bn_connect_btn_sensitive.set(True)

        def _destroy_and_hide_dialog(self) -> None:
            self._sever_model_and_view()
            self._view.hide()
            self._parent._active_change_camera_dialog_presenter = None

        def _sever_model_and_view(self) -> None:
            for ec in self.__event_connections:
                ec.disconnect()

    def __init__(self, impl: USBCameraImageAcquisitionImpl, view: USBCameraImageAcquisitionImplView) -> None:
        self._impl = impl
        self._view = view
        self._active_change_camera_dialog_presenter = None  # type: Optional[USBCameraImageAcquisitionImplPresenter.ChangeCameraDialogPresenter]

        self.__event_connections = [
            self._view.on_change_camera_btn_clicked.connect(self._hdl_view_change_camera_btn_clicked, immediate=True)
        ]

        self.__data_bindings = [
            Binding(self._impl.bn_current_camera_index, self._view.bn_current_camera_index),
            Binding(self._impl.bn_num_frames, self._view.bn_num_frames),
            Binding(self._impl.bn_frame_interval, self._view.bn_frame_interval)
        ]

    def _hdl_view_change_camera_btn_clicked(self) -> None:
        if self._active_change_camera_dialog_presenter:
            # Change camera dialog is already active.
            return

        dlg_view = self._view.show_change_camera_dialog()
        dlg_presenter = USBCameraImageAcquisitionImplPresenter.ChangeCameraDialogPresenter(self, self._impl, dlg_view)

        # Keep a reference to the dialog presenter so that it is not garbage collected.
        self._active_change_camera_dialog_presenter = dlg_presenter

    def destroy(self) -> None:
        for ec in self.__event_connections:
            ec.disconnect()

        for db in self.__data_bindings:
            db.unbind()


# Root view and presenter.

ImplType = TypeVar('ImplType', bound=ImageAcquisitionImplType)


class ImageAcquisitionRootView(Generic[ImplType], GtkWidgetView[Gtk.Grid]):
    STYLE = '''
    .small-combobox .combo {
        min-height: 0px;
        min-width: 0px;
    }
    '''

    _STYLE_PROV = Gtk.CssProvider()
    _STYLE_PROV.load_from_data(bytes(STYLE, 'utf-8'))
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), _STYLE_PROV, Gtk.STYLE_PROVIDER_PRIORITY_USER)

    def __init__(self, create_view_for_impl_type: Callable[[ImageAcquisitionImplType], GtkWidgetView]) -> None:
        self.widget = Gtk.Grid(margin=10, column_spacing=10, row_spacing=10)

        self._create_view_for_impl_type = create_view_for_impl_type
        self._combobox_id_to_impl_type = {}  # type: MutableMapping[str, ImageAcquisitionImplType]
        self._current_config_subview = None  # type: Optional[GtkWidgetView]

        user_input_impl_type_lbl = Gtk.Label('Image source:', xalign=0)
        self.widget.add(user_input_impl_type_lbl)
        self._user_input_impl_type_combobox = Gtk.ComboBoxText()
        self._user_input_impl_type_combobox.get_style_context().add_class('small-combobox')
        self.widget.attach_next_to(self._user_input_impl_type_combobox, user_input_impl_type_lbl, Gtk.PositionType.RIGHT, 1, 1)

        self.widget.attach(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL, hexpand=True), 0, 1, 3, 1)
        # Add a filler widget for layout reasons.
        self.widget.attach(Gtk.Label(hexpand=True), 2, 0, 1, 1)

        self._config_subview_container = Gtk.Box()
        self.widget.attach(self._config_subview_container, 0, 2, 3, 1)

        self.widget.show_all()

        self.bn_actual_user_input_impl_type = AtomicBindableAdapter()  # type: AtomicBindable[Optional[str]]
        link_atomic_bn_adapter_to_g_prop(self.bn_actual_user_input_impl_type, self._user_input_impl_type_combobox,
                                         'active-id')
        self.bn_user_input_impl_type = AtomicBindableVar(None)  # type: AtomicBindable[Optional[ImageAcquisitionImplType]]
        Binding(self.bn_actual_user_input_impl_type, self.bn_user_input_impl_type,
                mitm=AtomicBindingMITM(to_dst=self._impl_type_from_combobox_id,
                                       to_src=self._combobox_id_from_impl_type))

    def _impl_type_from_combobox_id(self, combobox_id: Optional[str]) -> Optional[ImageAcquisitionImplType]:
        if combobox_id is None:
            return None

        return self._combobox_id_to_impl_type[combobox_id]

    def _combobox_id_from_impl_type(self, impl_type: ImageAcquisitionImplType) -> Optional[str]:
        combobox_id = None  # type: Optional[str]
        for candidate_combobox_id, candidate_impl_type in self._combobox_id_to_impl_type.items():
            if candidate_impl_type is impl_type:
                combobox_id = candidate_combobox_id

        return combobox_id

    def configure_for(self, impl_type: ImplType) -> Any:
        new_config_subview = self._create_view_for_impl_type(impl_type)
        self._set_config_subview(new_config_subview)
        return new_config_subview

    def _set_config_subview(self, view: GtkWidgetView) -> None:
        old_config_subview = self._current_config_subview
        if old_config_subview is not None:
            old_config_subview.widget.destroy()
            self._current_config_subview = None

        self._config_subview_container.add(view.widget)
        self._current_config_subview = view

    def set_available_types(self, impl_types: Sequence[ImageAcquisitionImplType]) -> None:
        self._user_input_impl_type_combobox.remove_all()
        self._combobox_id_to_impl_type = {}

        for impl_type in impl_types:
            self._user_input_impl_type_combobox.append(impl_type.name, impl_type.display_name)
            self._combobox_id_to_impl_type[impl_type.name] = impl_type


class ImageAcquisitionRootPresenter(Generic[ImplType]):
    def __init__(self, image_acquisition: ImageAcquisition,
                 create_presenter_for_impl_and_view: Callable[[ImageAcquisitionImpl, Any], Destroyable],
                 available_types: Sequence[ImplType],
                 view: ImageAcquisitionRootView) -> None:
        self._image_acquisition = image_acquisition
        self._view = view
        self._create_presenter_for_impl_and_view = create_presenter_for_impl_and_view
        self._current_subpresenter = None  # type: Optional[Destroyable]

        self._view.set_available_types(available_types)

        self.__event_connections = [
            self._image_acquisition.bn_type.on_changed.connect(self.hdl_image_acquisition_type_changed, immediate=True)
        ]

        self.__data_bindings = [
            Binding(self._image_acquisition.bn_type, self._view.bn_user_input_impl_type)
        ]

        # Call the handler to connect the existing image acquisition implementation to the view.
        self.hdl_image_acquisition_type_changed()

    def hdl_image_acquisition_type_changed(self) -> None:
        old_subpresenter = self._current_subpresenter
        if old_subpresenter is not None:
            old_subpresenter.destroy()
            self._current_subpresenter = None

        new_type = self._image_acquisition.type
        if new_type is None:
            return

        new_child_view = self._view.configure_for(new_type)
        new_subpresenter = self._create_presenter_for_impl_and_view(self._image_acquisition.impl, new_child_view)
        self._current_subpresenter = new_subpresenter

    def destroy(self) -> None:
        for ec in self.__event_connections:
            ec.disconnect()

        for db in self.__data_bindings:
            db.unbind()

        if self._current_subpresenter is not None:
            self._current_subpresenter.destroy()


class ImageAcquisitionSpeaker(Speaker):
    _AVAILABLE_IMAGE_ACQUISITION_TYPES = tuple(DefaultImageAcquisitionImplType)
    _CONFIG_SUBVIEW_FACTORY = create_view_for_impl_type
    _CONFIG_SUBPRESENTER_FACTORY = create_presenter_for_impl_and_view

    def __init__(self, image_acquisition: ImageAcquisition, content_stack: StackModel) -> None:
        super().__init__()

        self._image_acquisition = image_acquisition
        self._content_stack = content_stack

        self._root_view = ImageAcquisitionRootView(ImageAcquisitionSpeaker._CONFIG_SUBVIEW_FACTORY)
        self._root_presenter = None  # type: Optional[ImageAcquisitionRootPresenter]

        self._root_view_cskey = object()
        self._content_stack.add_child(self._root_view_cskey, self._root_view)

    def do_activate(self) -> None:
        self._root_presenter = ImageAcquisitionRootPresenter(
            image_acquisition=self._image_acquisition,
            create_presenter_for_impl_and_view=ImageAcquisitionSpeaker._CONFIG_SUBPRESENTER_FACTORY,
            available_types=ImageAcquisitionSpeaker._AVAILABLE_IMAGE_ACQUISITION_TYPES,
            view=self._root_view
        )

        # Make root view visible.
        self._content_stack.visible_child_key = self._root_view_cskey

    def do_deactivate(self) -> None:
        assert self._root_presenter is not None
        self._root_presenter.destroy()
