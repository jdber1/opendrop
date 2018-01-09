from abc import abstractmethod
import math
from typing import Optional, Tuple

import cairo
import cv2
import numpy as np
from gi.repository import Gtk, Gdk

from opendrop.observer.bases import ObserverPreview
from opendrop.observer.types.camera import CameraObserverPreview
from opendrop.observer.types.image_slideshow import ImageSlideshowObserverPreview
from opendrop.gtk_specific.misc import pixbuf_from_array
from opendrop.widgets.integer_entry import IntegerEntry


class ObserverPreviewControllerContext:
    def __init__(self, preview: 'ObserverPreview', extern_controls_area: Gtk.Container):
        self.preview = preview
        self.extern_controls_area = extern_controls_area


class ObserverPreviewController:
    @staticmethod
    @abstractmethod
    def can_control(ctx: ObserverPreviewControllerContext) -> bool: pass

    @classmethod
    def control(cls, ctx: ObserverPreviewControllerContext) -> 'ObserverPreviewController':
        for controller_cls in cls.__subclasses__():
            if controller_cls.can_control(ctx):
                return controller_cls(ctx)


class CameraObserverPreviewController(ObserverPreviewController):
    _controls = type(None)

    def __init__(self, ctx: ObserverPreviewControllerContext):
        self.ctx = ctx

        controls = Gtk.Box()

        label = Gtk.Label('Live Preview')
        controls.pack_start(label, expand=True, fill=False, padding=0)

        ctx.extern_controls_area.pack_start(controls, expand=False, fill=False, padding=10)

    @staticmethod
    def can_control(ctx: ObserverPreviewControllerContext) -> bool:
        return isinstance(ctx.preview, CameraObserverPreview)


# add ability to draw over, image filter
class ImageSlideshowObserverPreviewController(ObserverPreviewController):
    _controls = type(None)

    def __init__(self, ctx: ObserverPreviewControllerContext):
        self.ctx = ctx  # type: ObserverPreviewControllerContext

        self._preview_index = 0  # type: int
        self.preview_length = self.ctx.preview.num_images  # type: int

        controls = Gtk.Box()

        vbox = Gtk.VBox()

        grid = Gtk.Grid(column_spacing=5)

        left_btn = Gtk.Button.new_from_icon_name('media-skip-backward', Gtk.IconSize.BUTTON)  # type: Gtk.Button
        left_btn.connect('clicked', self.handle_left_btn_clicked)

        grid.attach(left_btn, 0, 0, 1, 1)

        entry = IntegerEntry(width_chars=int(math.log10(self.preview_length or 1)) + 1)
        entry.connect('activate', self.handle_entry_activate)

        grid.attach(entry, 1, 0, 1, 1)

        self.entry = entry

        total_images_label = Gtk.Label("of {}".format(self.preview_length))

        grid.attach(total_images_label, 2, 0, 1, 1)

        right_btn = Gtk.Button.new_from_icon_name('media-skip-forward', Gtk.IconSize.BUTTON)  # type: Gtk.Button
        right_btn.connect('clicked', self.handle_right_btn_clicked)

        grid.attach(right_btn, 3, 0, 1, 1)

        vbox.pack_start(grid, expand=True, fill=False, padding=0)

        controls.pack_start(vbox, expand=False, fill=False, padding=0)

        ctx.extern_controls_area.pack_start(controls, expand=False, fill=False, padding=10)

        # Since UI is now created, trigger the preview_index setter to sync up the UI element text values
        self.preview_index = self.preview_index

    def handle_left_btn_clicked(self, widget: Gtk.Widget) -> None:
        self.preview_index_increment(-1)

    def handle_entry_activate(self, widget: Gtk.Widget) -> None:
        text = widget.props.text

        index = int(text) - 1

        index = max(0, min(self.preview_length - 1, index))

        self.preview_index = index

    def handle_right_btn_clicked(self, widget: Gtk.Widget) -> None:
        self.preview_index_increment(1)

    def preview_index_increment(self, by: int) -> None:
        self.preview_index = (self.preview_index + by) % self.preview_length

    @property
    def preview_index(self) -> int:
        return self._preview_index

    @preview_index.setter
    def preview_index(self, value: int) -> None:
        self._preview_index = value
        self.entry.props.text = str(value + 1)

        self.ctx.preview.show(value)

    @staticmethod
    def can_control(ctx: ObserverPreviewControllerContext) -> bool:
        return isinstance(ctx.preview, ImageSlideshowObserverPreview)


class ObserverPreviewViewer(Gtk.VBox):

    __gtype_name__ = 'ObserverPreviewViewer'

    def __init__(self, preview: Optional[ObserverPreview] = None) -> None:
        super().__init__()

        # initialise attributes
        self._zoom_fill = True  # type: bool
        self.preview = None  # type: Optional[ObserverPreview]
        self.preview_image = None  # type: Optional[np.ndarray]

        # preview_drawing_area
        preview_drawing_area = Gtk.DrawingArea()  # type: Gtk.DrawingArea
        preview_drawing_area.connect('draw', self.handle_preview_drawing_area_draw)

        self.pack_start(preview_drawing_area, expand=True, fill=True, padding=0)

        self.preview_drawing_area = preview_drawing_area  # type: Gtk.DrawingArea

        # controls_area_container
        controls_area_container = Gtk.Box()  # type: Gtk.Box
        controls_area_container.set_name('controls_area_container')

        plugin_area_container_css = Gtk.CssProvider()  # type: Gtk.CssProvider
        plugin_area_container_css.load_from_data(bytes('''
            #controls_area_container {
                background-color: gainsboro;
            }
        ''', encoding='utf-8'))
        controls_area_container.get_style_context() \
                               .add_provider(plugin_area_container_css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self.pack_start(controls_area_container, expand=False, fill=False, padding=0)

        # controls_area
        controls_area = Gtk.HBox(spacing=5)  # type: Gtk.HBox
        controls_area.props.margin = 5  # type: int

        controls_area_container.pack_start(controls_area, expand=True, fill=True, padding=0)

        self.controls_area = controls_area  # type: Gtk.HBox

        # zoom_btn_container
        zoom_btn_container = Gtk.VBox()  # type: Gtk.VBox
        controls_area.pack_end(zoom_btn_container, expand=False, fill=False, padding=0)

        # zoom_btn_lbl
        zoom_btn_lbl = Gtk.Label('Zoom:')  # type: Gtk.Label

        zoom_btn_container.pack_start(zoom_btn_lbl, expand=False, fill=False, padding=0)

        # zoom_btn
        zoom_btn = Gtk.Button(label='Fill')  # type: Gtk.Button
        zoom_btn.connect('clicked', self.handle_zoom_btn_clicked)

        zoom_btn_container.pack_start(zoom_btn, expand=False, fill=False, padding=0)

        # extern_controls_area
        extern_controls_area = Gtk.HBox(spacing=5)  # type: Gtk.HBox
        controls_area.pack_start(extern_controls_area, expand=True, fill=True, padding=0)

        self.extern_controls_area = extern_controls_area  # type: Gtk.HBox

        self.set_preview(preview)

        self.show_all()

    @property
    def zoom_fill(self) -> bool:
        return self._zoom_fill

    @zoom_fill.setter
    def zoom_fill(self, value: bool) -> None:
        self._zoom_fill = value

        self.redraw_preview()

    def set_preview(self, preview: ObserverPreview) -> None:
        if self.preview:
            self.preview.disconnect('on_update', self.handle_preview_on_update)

        if preview is not None:
            preview.connect('on_update', self.handle_preview_on_update)

        self.preview = preview
        self.preview_image = None

        self.load_controller()

        self.redraw_preview()

    def load_controller(self) -> None:
        self.extern_controls_area.foreach(lambda w: w.destroy())

        ObserverPreviewController.control(self.create_context())

        self.extern_controls_area.show_all()

    def create_context(self) -> ObserverPreviewControllerContext:
        return ObserverPreviewControllerContext(self.preview, self.extern_controls_area)

    def handle_preview_on_update(self, image: np.ndarray) -> None:
        self.preview_image = image

        self.redraw_preview()

    def redraw_preview(self) -> None:
        self.preview_drawing_area.queue_draw()

    def handle_preview_drawing_area_draw(self, widget: Gtk.Widget, cr: cairo.Context) -> None:
        cr.set_source_rgb(0, 0, 0)
        cr.paint()

        if self.preview_image is None:
            cr.set_source_rgb(255, 255, 255)
            cr.move_to(10, 20)
            cr.show_text('No preview')

            return

        widget_size = (widget.get_allocated_width(), widget.get_allocated_height())  # type: Tuple[int, int]
        widget_aspect = widget_size[0]/widget_size[1]  # type: float

        image_size = self.preview_image.shape[1], self.preview_image.shape[0]  # type: Tuple[int, int]
        image_aspect = image_size[0]/image_size[1]  # type: float
        scale_factor = 1  # type: int

        if self.zoom_fill and (widget_aspect > image_aspect) or not self.zoom_fill and (widget_aspect <= image_aspect):
            scale_factor = widget_size[0]/image_size[0]
        else:
            scale_factor = widget_size[1]/image_size[1]

        im = cv2.resize(self.preview_image, dsize=(0, 0), fx=scale_factor, fy=scale_factor)  # type: np.ndarray

        offset = (
            widget_size[0]/2 - (image_size[0] * scale_factor)/2,
            widget_size[1]/2 - (image_size[1] * scale_factor)/2
        )  # type: Tuple[float, float]

        Gdk.cairo_set_source_pixbuf(cr, pixbuf_from_array(im), *offset)
        cr.paint()

    def handle_zoom_btn_clicked(self, widget: Gtk.Widget) -> None:
        if self.zoom_fill:
            self.zoom_fill = False

            widget.props.label = 'Fill'
        else:
            self.zoom_fill = True

            widget.props.label = 'Fit'
