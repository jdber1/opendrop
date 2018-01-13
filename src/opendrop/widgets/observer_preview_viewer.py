from abc import abstractmethod
import math
from typing import Optional, Tuple

import cairo
import cv2
import numpy as np
from gi.repository import Gtk, Gdk, GObject

from opendrop.image_filter.image_filter_group import ImageFilterGroup
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
    def can_control(ctx: ObserverPreviewControllerContext) -> bool:
        pass

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

        self.filters = ImageFilterGroup()

        # initialise attributes
        self._zoom_fill = True  # type: bool
        self.preview = None  # type: Optional[ObserverPreview]
        self.preview_image = None  # type: Optional[np.ndarray]

        # preview_drawing_area
        preview_drawing_area = Gtk.DrawingArea()  # type: Gtk.DrawingArea
        preview_drawing_area.connect('draw', self._handle_preview_drawing_area_draw)

        preview_drawing_area.add_events(
            Gdk.EventMask.POINTER_MOTION_MASK
            | Gdk.EventMask.BUTTON_PRESS_MASK
        )

        preview_drawing_area.connect('motion-notify-event', self._handle_da_motion_notify_event)

        preview_drawing_area.connect('button-press-event', self._handle_da_button_press_event)

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
        self.zoom_btn = Gtk.Button()  # type: Gtk.Button
        self.zoom_btn.connect('clicked', self._handle_zoom_btn_clicked)

        # Invoke the setter so it updates zoom_btn's label
        self.zoom_fill = self.zoom_fill

        zoom_btn_container.pack_start(self.zoom_btn, expand=False, fill=False, padding=0)

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

        self.zoom_btn.props.label = ('Fill', 'Fit')[value]

        self.redraw_preview()

    def set_preview(self, preview: ObserverPreview) -> None:
        if self.preview:
            self.preview.disconnect('on_update', self._handle_preview_on_update)

        if preview is not None:
            preview.connect('on_update', self._handle_preview_on_update)

        self.preview = preview
        self.preview_image = None

        self._load_controller()

        self.redraw_preview()

    def _load_controller(self) -> None:
        self.extern_controls_area.foreach(lambda w: w.destroy())

        ObserverPreviewController.control(self._create_context())

        self.extern_controls_area.show_all()

    def _create_context(self) -> ObserverPreviewControllerContext:
        return ObserverPreviewControllerContext(self.preview, self.extern_controls_area)

    def _handle_preview_on_update(self, image: np.ndarray) -> None:
        self.preview_image = image

        self.redraw_preview()

    def redraw_preview(self) -> None:
        self.preview_drawing_area.queue_draw()

    def _handle_preview_drawing_area_draw(self, widget: Gtk.Widget, cr: cairo.Context) -> None:
        # Fill drawing area background black
        cr.set_source_rgb(0, 0, 0)
        cr.paint()

        # If there's no preview image, draw a placeholder graphic
        if self.preview_image is None:
            cr.set_source_rgb(255, 255, 255)
            cr.move_to(10, 20)
            cr.show_text('No preview')
            return

        im_draw_size = self._preview_image_draw_size  # type: Tuple[int, int]
        im_draw_offset = self._preview_image_draw_offset  # type: Tuple[int, int]

        im = cv2.resize(self.preview_image, dsize=im_draw_size)  # type: np.ndarray

        # Apply the custom filters
        im = self.filters.apply(im)

        Gdk.cairo_set_source_pixbuf(cr, pixbuf_from_array(im), *im_draw_offset)
        cr.paint()

    def _handle_zoom_btn_clicked(self, widget: Gtk.Widget) -> None:
        self.zoom_fill ^= True

    def _handle_da_motion_notify_event(self, widget: Gtk.Widget, event: Gdk.EventMotion):
        event.x, event.y = self._image_rel_pos_from_da_abs_pos(event.x, event.y)

        self.emit('viewer-motion-notify-event', event)

    def _handle_da_button_press_event(self, widget: Gtk.Widget, event: Gdk.EventButton):
        event.x, event.y = self._image_rel_pos_from_da_abs_pos(event.x, event.y)

        self.emit('viewer-button-press-event', event)

    def _image_rel_pos_from_da_abs_pos(self, x: float, y: float) -> Tuple[float, float]:
        size = self._preview_image_draw_size  # type: Tuple[int, int]
        offset = self._preview_image_draw_offset  # type: Tuple[int, int]

        pos = (x - offset[0], y - offset[1])  # type: Tuple[float, float]

        pos = (pos[0]/size[0], pos[1]/size[1])

        return pos

    @property
    def _preview_image_draw_size(self) -> Tuple[int, int]:
        da = self.preview_drawing_area  # type: Gtk.DrawingArea

        da_size = (da.get_allocated_width(), da.get_allocated_height())  # type: Tuple[int, int]
        da_aspect = da_size[0] / da_size[1]  # type: float

        if self.preview_image is None:
            return da_size

        image_size = self.preview_image.shape[1], self.preview_image.shape[0]  # type: Tuple[int, int]
        image_aspect = image_size[0] / image_size[1]  # type: float

        if self.zoom_fill and (da_aspect > image_aspect) or not self.zoom_fill and (da_aspect <= image_aspect):
            scale_factor = da_size[0] / image_size[0]  # type: float
        else:
            scale_factor = da_size[1] / image_size[1]  # type: float

        return round(image_size[0] * scale_factor), round(image_size[1] * scale_factor)

    @property
    def _preview_image_draw_offset(self) -> Tuple[int, int]:
        if self.preview_image is None:
            return 0, 0

        da = self.preview_drawing_area  # type: Gtk.DrawingArea

        da_size = np.array((da.get_allocated_width(), da.get_allocated_height()))  # type: np.ndarray
        image_draw_size = np.array(self._preview_image_draw_size)  # type: np.ndarray

        offset = tuple(da_size/2 - image_draw_size/2)

        return offset


GObject.signal_new('viewer-motion-notify-event',
                   ObserverPreviewViewer, GObject.SIGNAL_RUN_LAST, GObject.TYPE_PYOBJECT, (GObject.TYPE_PYOBJECT,)
                   )
GObject.signal_new('viewer-button-press-event',
                   ObserverPreviewViewer, GObject.SIGNAL_RUN_LAST, GObject.TYPE_PYOBJECT, (GObject.TYPE_PYOBJECT,)
                   )
