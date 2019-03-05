from typing import Optional, Callable, Any

from gi.repository import Gtk, Gdk

from opendrop.app.common.model.image_acquisition.default_types import \
    ImageSequenceImageAcquisitionPreviewConfig
from opendrop.component.gtk_widget_view import GtkWidgetView
from opendrop.mytypes import Destroyable
from opendrop.utility.bindable import Bindable, BoxBindable
from opendrop.utility.events import Event


# Dependency injection stuff

def create_preview_config_presenter_for_config_and_view(config: Any, view: Optional[GtkWidgetView]) \
        -> Optional[Destroyable]:
    if isinstance(config, ImageSequenceImageAcquisitionPreviewConfig) \
            and isinstance(view, LocalImagesImageAcquisitionPreviewConfigView):
        return LocalImagesImageAcquisitionPreviewConfigPresenter(config, view)
    else:
        return None


def create_preview_config_view_for_config(config: Any) -> Optional[GtkWidgetView]:
    if isinstance(config, ImageSequenceImageAcquisitionPreviewConfig):
        return LocalImagesImageAcquisitionPreviewConfigView()
    else:
        return None


# Local images

class LocalImagesImageAcquisitionPreviewConfigView(GtkWidgetView[Gtk.Grid]):
    STYLE = '''
    .local-images-preview-config-lr-btn {
         min-height: 0px;
         min-width: 20px;
         padding: 6px 4px 6px 4px;
    }
    '''

    _STYLE_PROV = Gtk.CssProvider()
    _STYLE_PROV.load_from_data(bytes(STYLE, 'utf-8'))
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), _STYLE_PROV, Gtk.STYLE_PROVIDER_PRIORITY_USER)

    def __init__(self) -> None:
        self.widget = Gtk.Grid(margin=5, column_spacing=5)

        explain_lbl = Gtk.Label('Showing image:')
        self.widget.attach(explain_lbl, 0, 0, 1, 1)

        left_btn = Gtk.Button('<')
        left_btn.get_style_context().add_class('local-images-preview-config-lr-btn')
        right_btn = Gtk.Button('>')
        right_btn.get_style_context().add_class('local-images-preview-config-lr-btn')
        self._index_lbl = Gtk.Label()

        self.widget.attach(left_btn, 1, 0, 1, 1)
        self.widget.attach(right_btn, 3, 0, 1, 1)
        self.widget.attach(self._index_lbl, 2, 0, 1, 1)

        self.widget.show_all()

        self.on_left_btn_clicked = Event()
        self.on_right_btn_clicked = Event()

        left_btn.connect('clicked', lambda *_: self.on_left_btn_clicked.fire())
        right_btn.connect('clicked', lambda *_: self.on_right_btn_clicked.fire())

        self.bn_num_images = BoxBindable(0)  # type: Bindable[int]
        self.bn_index = BoxBindable(0)  # type: Bindable[int]

        self.bn_num_images.on_changed.connect(self._update_index_lbl)
        self.bn_index.on_changed.connect(self._update_index_lbl)

    def _update_index_lbl(self) -> None:
        # The '+1' is to convert 0-based indexing to the more typical everyday 1-based indexing.
        self._index_lbl.props.label = '{} of {}'.format(self.bn_index.get() + 1, self.bn_num_images.get())


class LocalImagesImageAcquisitionPreviewConfigPresenter:
    def __init__(self, config: ImageSequenceImageAcquisitionPreviewConfig,
                 view: LocalImagesImageAcquisitionPreviewConfigView) -> None:
        self._config = config
        self._view = view

        self.__event_connections = [
            self._view.on_left_btn_clicked.connect(self._hdl_view_left_btn_clicked),
            self._view.on_right_btn_clicked.connect(self._hdl_view_right_btn_clicked)
        ]

        self.__data_bindings = [
            self._config.bn_num_images.bind_to(self._view.bn_num_images),
            self._config.bn_index.bind_to(self._view.bn_index)
        ]

    def _hdl_view_right_btn_clicked(self) -> None:
        index = self._config.bn_index.get()
        num_images = self._config.bn_num_images.get()

        next_index = (index + 1) % num_images
        self._config.bn_index.set(next_index)

    def _hdl_view_left_btn_clicked(self) -> None:
        index = self._config.bn_index.get()
        num_images = self._config.bn_num_images.get()

        next_index = (index - 1) % num_images
        self._config.bn_index.set(next_index)

    def destroy(self) -> None:
        for ec in self.__event_connections:
            ec.disconnect()

        for db in self.__data_bindings:
            db.unbind()


# Preview config container view

class ImageAcquisitionPreviewConfigView(GtkWidgetView[Gtk.Grid]):
    def __init__(self, create_preview_config_view_for_config: Callable[[Any], GtkWidgetView] \
            = create_preview_config_view_for_config) -> None:
        self.widget = Gtk.Grid()
        self.widget.show_all()

        self._create_preview_config_view_for_config = create_preview_config_view_for_config

        self.impl = None  # type: Optional[GtkWidgetView]

    def configure_for_config(self, config: Any) -> GtkWidgetView:
        # Remove the old implementation
        old_impl = self.impl
        if old_impl is not None:
            old_impl.widget.destroy()

        self.impl = self._create_preview_config_view_for_config(config)
        if self.impl is not None:
            self.widget.add(self.impl.widget)
            self.impl.widget.show()

        return self.impl


# CamelCase to make usage of the function more like constructing an object.
ImageAcquisitionPreviewConfigPresenter = create_preview_config_presenter_for_config_and_view
