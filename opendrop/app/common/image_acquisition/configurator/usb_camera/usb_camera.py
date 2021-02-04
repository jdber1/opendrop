from typing import Optional

from injector import inject
from gi.repository import Gtk, GObject

# These widgets are used in templates, import them to make sure they're registered with the GLib type system.
from opendrop.widgets.integer_entry import IntegerEntry
from opendrop.widgets.float_entry import FloatEntry

from opendrop.appfw import Presenter, ComponentFactory, TemplateChild, component, install
from opendrop.app.common.services.acquisition import USBCameraAcquirer


@component(
    template_path='./usb_camera.ui',
)
class ImageAcquisitionConfiguratorUSBCameraPresenter(Presenter):
    choose_camera_button: TemplateChild[Gtk.Button] = TemplateChild('choose_camera_button')

    @inject
    def __init__(self, cf: ComponentFactory) -> None:
        self.cf = cf

    def after_view_init(self) -> None:
        self.event_connections = [
            self.acquirer.bn_camera_index.on_changed.connect(self.acquirer_camera_index_changed),
            self.acquirer.bn_num_frames.on_changed.connect(self.acquirer_num_frames_changed),
            self.acquirer.bn_frame_interval.on_changed.connect(self.acquirer_frame_interval_changed),
        ]

        self.acquirer_camera_index_changed()
        self.acquirer_num_frames_changed()
        self.acquirer_frame_interval_changed()

    def acquirer_camera_index_changed(self) -> None:
        self.notify('camera-description')

    def acquirer_num_frames_changed(self) -> None:
        self.notify('num-frames')
        self.notify('frame-interval-enabled')

    def acquirer_frame_interval_changed(self) -> None:
        self.notify('frame-interval')

    @GObject.Property(flags=GObject.ParamFlags.READWRITE|GObject.ParamFlags.EXPLICIT_NOTIFY)
    def num_frames(self) -> Optional[int]:
        return self.acquirer.bn_num_frames.get()

    @num_frames.setter
    def num_frames(self, num: Optional[int]) -> None:
        self.acquirer.bn_num_frames.set(num)

    @GObject.Property(flags=GObject.ParamFlags.READWRITE|GObject.ParamFlags.EXPLICIT_NOTIFY)
    def frame_interval(self) -> Optional[float]:
        return self.acquirer.bn_frame_interval.get()

    @frame_interval.setter
    def frame_interval(self, interval: Optional[float]) -> None:
        self.acquirer.bn_frame_interval.set(interval)

    @GObject.Property(type=bool, default=False, flags=GObject.ParamFlags.READABLE|GObject.ParamFlags.EXPLICIT_NOTIFY)
    def frame_interval_enabled(self) -> bool:
        return self.acquirer.bn_num_frames.get() != 1

    @GObject.Property(type=str, flags=GObject.ParamFlags.READABLE|GObject.ParamFlags.EXPLICIT_NOTIFY)
    def camera_description(self) -> str:
        camera_index = self.acquirer.bn_camera_index.get()

        if camera_index is None:
            camera_desc = '<None>'
        else:
            camera_desc = str(camera_index)

        return camera_desc

    def choose_camera_button_clicked(self, *_) -> None:
        if hasattr(self, 'choose_camera_dialog'): return

        def hdl_response(dialog: Gtk.Dialog, response: Gtk.ResponseType) -> None:
            if response != Gtk.ResponseType.APPLY:
                self.choose_camera_dialog.destroy()
                del self.choose_camera_dialog
                return

            arg = self.choose_camera_dialog.props.argument

            if self.choose_camera_dialog.props.initial_argument == arg:
                # User did not change argument.
                self.choose_camera_dialog.destroy()
                del self.choose_camera_dialog
                return

            try:
                arg = int(arg)
            except ValueError:
                pass

            if arg == '':
                self.acquirer.remove_current_camera()
            else:
                try:
                    self.acquirer.open_camera(arg)
                except ValueError as e:
                    self.choose_camera_dialog.props.error_text = e.args[0]
                    return

            self.choose_camera_dialog.destroy()
            del self.choose_camera_dialog

        current_argument = self.acquirer.bn_camera_index.get()

        self.choose_camera_dialog = self.cf.create(
            'ImageAcquisitionConfiguratorUSBCameraChooser',
            transient_for=self.get_window(),
            initial_argument=str(current_argument) if current_argument is not None else '',
            modal=True,
        )

        self.choose_camera_dialog.connect('response', hdl_response)
        self.choose_camera_dialog.show()

    def get_window(self) -> Optional[Gtk.Window]:
        toplevel = self.host.get_toplevel()
        if isinstance(toplevel, Gtk.Window):
            return toplevel
        else:
            return None

    @install
    @GObject.Property(flags=GObject.ParamFlags.READWRITE|GObject.ParamFlags.CONSTRUCT_ONLY)
    def acquirer(self) -> USBCameraAcquirer:
        return self._acquirer

    @acquirer.setter
    def acquirer(self, acquirer: USBCameraAcquirer) -> None:
        self._acquirer = acquirer

    def destroy(self, *_) -> None:
        for conn in self.event_connections:
            conn.disconnect()
