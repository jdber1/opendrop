from typing import Optional, Callable, Generic, TypeVar, Tuple, Sequence

import numpy as np
from gi.repository import Gtk, Gdk

from opendrop.app.common.content.image_processing.stage import StageView, StagePresenter
from opendrop.app.common.model.image_acquisition.image_acquisition import ImageAcquisitionPreview
from opendrop.component.gtk_widget_view import GtkWidgetView
from opendrop.component.image_acquisition_preview_config import ImageAcquisitionPreviewConfigView, \
    ImageAcquisitionPreviewConfigPresenter
from opendrop.mytypes import Image
from opendrop.utility.bindable.bindable import AtomicBindable, AtomicBindableAdapter
from opendrop.utility.bindablegext.bindable import GObjectPropertyBindable
from opendrop.utility.geometry import Vector2
from opendrop.utility.gmisc import pixbuf_from_array
from opendrop.widgets.render import Render
from opendrop.widgets.render.objects import PixbufFill, Polyline, Rectangle


# Render object wrapper views


class RectangleView:
    def __init__(self, rectangle: Rectangle) -> None:
        self.bn_extents = GObjectPropertyBindable(rectangle, 'extents')


class MaskHighlightView:
    def __init__(self, ro: PixbufFill, color: Tuple[float, float, float, float] = (127, 127, 255, 255)) -> None:
        self._ro = ro
        self._color = color
        self.bn_mask = AtomicBindableAdapter(setter=self._set_mask)  # type: AtomicBindable[Optional[Image]]

    def _set_mask(self, mask: Optional[Image]) -> None:
        if mask is None:
            self._ro.props.pixbuf = None
            return

        surface = np.zeros(mask.shape + (4,), dtype='uint8')
        surface[mask.astype(bool)] = self._color

        self._ro.props.pixbuf = pixbuf_from_array(surface)


class PolylineView:
    def __init__(self, ro: Polyline) -> None:
        self._ro = ro
        self.bn_polyline = GObjectPropertyBindable(self._ro, 'polyline')  # type: AtomicBindable[Optional[Sequence[Vector2[float]]]]


class ImageProcessingFormView(GtkWidgetView[Gtk.Stack]):
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
        self.widget = Gtk.Stack()

        self._no_preview_error = Gtk.Label('Failed to create image acquisition preview.')
        self.widget.add(self._no_preview_error)

        self._main = Gtk.Grid()
        self.widget.add(self._main)

        stage_and_toolbar_ctn = Gtk.Grid(row_spacing=10)
        self._main.attach(stage_and_toolbar_ctn, 0, 0, 1, 1)

        define_regions_lbl = Gtk.Label(margin_left=10, margin_right=10, margin_top=10, xalign=0)
        define_regions_lbl.set_markup('<b>Preview, and define features:</b>')
        stage_and_toolbar_ctn.attach(define_regions_lbl, 0, 0, 1, 1)

        self._toolbar_area = Gtk.Grid(margin_left=10, margin_right=10, column_spacing=5)
        stage_and_toolbar_ctn.attach(self._toolbar_area, 0, 1, 1, 1)

        self._stage_render = Render(hexpand=True, vexpand=True)
        stage_and_toolbar_ctn.attach(self._stage_render, 0, 2, 1, 1)

        preview_config_ctn = Gtk.Grid()
        stage_and_toolbar_ctn.attach(preview_config_ctn, 0, 3, 1, 1)

        self._main.attach(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), 0, 1, 1, 1)

        self._extras_area = Gtk.Grid(margin=10, row_spacing=10)
        self._main.attach(self._extras_area, 0, 2, 1, 1)

        self.widget.show_all()

        # Subviews

        # Image acquisition preview config view
        self.preview_config = ImageAcquisitionPreviewConfigView()
        preview_config_ctn.add(self.preview_config.widget)
        self.preview_config.widget.show()

        # Image acquisition preview view
        self.stage = StageView(render=self._stage_render)

    def show_no_preview_error(self) -> None:
        self.widget.set_visible_child(self._no_preview_error)

    def show_main(self) -> None:
        self.widget.set_visible_child(self._main)


ImageProcessingFormViewType = TypeVar('ImageProcessingFormViewType', bound=ImageProcessingFormView)


class ImageProcessingFormPresenter(Generic[ImageProcessingFormViewType]):
    def __init__(self, create_preview: Callable[[], Optional[ImageAcquisitionPreview]],
                 view: ImageProcessingFormViewType) -> None:
        self._create_preview = create_preview
        self._view = view

        self.__destroyed = False
        self.__cleanup_tasks = []

        preview = self._create_preview()

        if preview is None:
            self._view.show_no_preview_error()
            return

        self._view.show_main()

        self._preview = preview
        self.__cleanup_tasks.append(self._preview.destroy)

        # Preview config
        preview_config_model = self._preview.config
        config_view_impl = self._view.preview_config.configure_for_config(preview_config_model)
        preview_config = ImageAcquisitionPreviewConfigPresenter(preview_config_model, config_view_impl)
        if preview_config is not None:
            self.__cleanup_tasks.append(preview_config.destroy)

        # Stage
        self._stage = StagePresenter(self._view.stage)
        self.__cleanup_tasks.append(self._stage.destroy)

        event_connections = [
            self._preview.on_image_changed.connect(self._update_preview_image, ignore_args=True)]
        self.__cleanup_tasks.extend(ec.disconnect for ec in event_connections)

        self._update_preview_image()

    def _update_preview_image(self):
        self._stage.bn_canvas_source.set(self._preview.image)

    def validate(self) -> bool:
        return True

    def destroy(self) -> None:
        assert not self.__destroyed
        for f in self.__cleanup_tasks:
            f()
        self.__destroyed = True
