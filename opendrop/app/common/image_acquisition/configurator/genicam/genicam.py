from typing import Optional

from injector import inject
from gi.repository import Gtk, GObject

# These widgets are used in templates, import them to make sure they're registered with the GLib type system.
from opendrop.widgets.integer_entry import IntegerEntry
from opendrop.widgets.float_entry import FloatEntry

from opendrop.appfw import Presenter, ComponentFactory, TemplateChild, component, install
from opendrop.app.common.services.acquisition import GenicamAcquirer


@component(
    template_path='./genicam.ui',
)
class ImageAcquisitionConfiguratorGenicamPresenter(Presenter):
    choose_camera_button = TemplateChild('choose_camera_button')  # type: TemplateChild[Gtk.Button]
    configure_camera_button = TemplateChild('configure_camera_button')  # type: TemplateChild[Gtk.Button]
    remove_camera_button = TemplateChild('remove_camera_button')  # type: TemplateChild[Gtk.Button]

    @inject
    def __init__(self, cf: ComponentFactory) -> None:
        self.cf = cf

    def after_view_init(self) -> None:
        self.event_connections = [
            self.acquirer.bn_camera_id.on_changed.connect(self.acquirer_camera_id_changed),
            self.acquirer.bn_num_frames.on_changed.connect(self.acquirer_num_frames_changed),
            self.acquirer.bn_frame_interval.on_changed.connect(self.acquirer_frame_interval_changed),
        ]

        self.acquirer_camera_id_changed()
        self.acquirer_num_frames_changed()
        self.acquirer_frame_interval_changed()

    def acquirer_camera_id_changed(self) -> None:
        self.update_camera_buttons()
        self.notify('camera-description')

    def acquirer_num_frames_changed(self) -> None:
        self.notify('num-frames')
        self.notify('frame-interval-enabled')

    def acquirer_frame_interval_changed(self) -> None:
        self.notify('frame-interval')

    def update_camera_buttons(self) -> None:
        camera_id = self.acquirer.bn_camera_id.get()

        if camera_id is None:
            self.choose_camera_button.show()
            self.configure_camera_button.hide()
            self.remove_camera_button.hide()
        else:
            self.choose_camera_button.hide()
            self.configure_camera_button.show()
            self.remove_camera_button.show()

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
        camera_id = self.acquirer.bn_camera_id.get()

        if camera_id is None:
            camera_desc = '<None>'
        else:
            for info in self.acquirer.enumerate_cameras():
                if info.camera_id == camera_id:
                    camera_desc = info.name
                    break
            else:
                camera_desc = '<Unknown>'

        return camera_desc

    def choose_camera_button_clicked(self, *_) -> None:
        if hasattr(self, 'choose_camera_dialog'): return

        def hdl_response(dialog: Gtk.Dialog, response: Gtk.ResponseType) -> None:
            try:
                if response != Gtk.ResponseType.APPLY: return

                camera_id = self.choose_camera_dialog.get_camera_id()
                if camera_id is None: return

                self.acquirer.open_camera(camera_id)
            finally:
                self.choose_camera_dialog.destroy()
                del self.choose_camera_dialog

        self.choose_camera_dialog = self.cf.create(
            'ImageAcquisitionConfiguratorGenicamCameraChooser',
            transient_for=self.get_window(),
            modal=True,
        )

        self.acquirer.update()
        cameras = {info.camera_id: info for info in self.acquirer.enumerate_cameras()}

        for info in cameras.values():
            self.choose_camera_dialog.append(
                camera_id=info.camera_id,
                vendor=info.vendor,
                model=info.model,
                name=info.name,
                tl_type=info.tl_type,
                version=info.version,
            )

        current_camera_id = self.acquirer.bn_camera_id.get()
        if current_camera_id in cameras:
            self.choose_camera_dialog.select_camera_id(current_camera_id)

        self.choose_camera_dialog.connect('response', hdl_response)
        self.choose_camera_dialog.show()

    def remove_camera_button_clicked(self, *_) -> None:
        self.acquirer.remove_current_camera()

    def configure_camera_button_clicked(self, *_) -> None:
        raise NotImplementedError

    def get_window(self) -> Optional[Gtk.Window]:
        toplevel = self.host.get_toplevel()
        if isinstance(toplevel, Gtk.Window):
            return toplevel
        else:
            return None

    @install
    @GObject.Property(flags=GObject.ParamFlags.READWRITE|GObject.ParamFlags.CONSTRUCT_ONLY)
    def acquirer(self) -> GenicamAcquirer:
        return self._acquirer

    @acquirer.setter
    def acquirer(self, acquirer: GenicamAcquirer) -> None:
        self._acquirer = acquirer

    def destroy(self, *_) -> None:
        for conn in self.event_connections:
            conn.disconnect()
