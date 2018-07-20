from enum import Enum
from typing import Optional, Tuple

import cairo
import cv2
import numpy as np
from gi.repository import Gtk, Gdk, GObject

from opendrop.gtk_specific.misc import pixbuf_from_array
from opendrop.image_filter.image_filter_group import ImageFilterGroup
from opendrop.observer.bases import ObserverPreview


class PreviewViewer(Gtk.DrawingArea):
    __gtype_name__ = 'PreviewViewer'

    class ZoomType(Enum):
        Fit = 0
        Fill = 1

        def next(self):
            return type(self)((self.value + 1) % len(type(self)))

        def __str__(self):
            return self.name

    def __init__(self, can_focus=True, **properties) -> None:
        # Property defaults
        self._preview = None  # type: Optional[ObserverPreview]
        self._zoom = PreviewViewer.ZoomType.Fit

        super().__init__(can_focus=can_focus, **properties)

        # Attributes
        #   public
        self.filters = ImageFilterGroup()

        #   private
        self._buffer = None  # type: Optional[np.ndarray]

        # Build widget
        self.add_events(
            Gdk.EventMask.POINTER_MOTION_MASK
            | Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.BUTTON_RELEASE_MASK
            | Gdk.EventMask.FOCUS_CHANGE_MASK
        )

        # Event handling

        self.connect('button-press-event', lambda *args: self.grab_focus())

        self.queue_draw()

        self.show_all()

    def rel_from_abs(self, abs_coord: Tuple[float, float]) -> Tuple[float, float]:
        size = self._preview_draw_size  # type: Tuple[int, int]
        offset = self._preview_draw_offset  # type: Tuple[int, int]

        rel_coord = (abs_coord[0] - offset[0], abs_coord[1] - offset[1])  # type: Tuple[float, float]

        rel_coord = (rel_coord[0]/size[0], rel_coord[1]/size[1])

        return rel_coord

    @GObject.Property
    def zoom(self) -> ZoomType:
        return self._zoom

    @zoom.setter
    def zoom(self, value: ZoomType) -> None:
        self._zoom = value

        self.queue_draw()

    @GObject.Property
    def preview(self) -> Optional[ObserverPreview]:
        return self._preview

    @preview.setter
    def preview(self, value: ObserverPreview) -> None:
        if self.preview is not None:
            self.preview.on_changed.disconnect_by_func(self._handle_preview_on_changed)

        if value is not None:
            value.on_changed.connect(self._handle_preview_on_changed)

        self._preview = value
        self._buffer = None

        self.queue_draw()

    @property
    def _preview_draw_size(self) -> Tuple[int, int]:
        self_size = (self.get_allocated_width(), self.get_allocated_height())  # type: Tuple[int, int]
        self_aspect = self_size[0] / self_size[1]  # type: float

        if self._buffer is None:
            return self_size

        image_size = self._buffer.shape[1], self._buffer.shape[0]  # type: Tuple[int, int]
        image_aspect = image_size[0] / image_size[1]  # type: float

        if self.zoom == PreviewViewer.ZoomType.Fill and (self_aspect > image_aspect) \
           or self.zoom == PreviewViewer.ZoomType.Fit and (self_aspect <= image_aspect):
            scale_factor = self_size[0] / image_size[0]  # type: float
        else:
            scale_factor = self_size[1] / image_size[1]  # type: float

        return round(image_size[0] * scale_factor), round(image_size[1] * scale_factor)

    @property
    def _preview_draw_offset(self) -> Tuple[int, int]:
        if self._buffer is None:
            return 0, 0

        self_size = np.array((self.get_allocated_width(), self.get_allocated_height()))  # type: np.ndarray
        image_draw_size = np.array(self._preview_draw_size)  # type: np.ndarray

        offset = tuple(self_size/2 - image_draw_size/2)

        return offset

    def do_draw(self, cr: cairo.Context) -> None:
        # Fill drawing area background black
        cr.set_source_rgb(0, 0, 0)
        cr.paint()

        # If there's no preview image, draw a placeholder graphic
        if self._buffer is None:
            cr.set_source_rgb(255, 255, 255)
            cr.move_to(10, 20)
            cr.show_text('No preview')

            return

        im_draw_size = self._preview_draw_size  # type: Tuple[int, int]
        im_draw_offset = self._preview_draw_offset  # type: Tuple[int, int]

        im = self._buffer
        im = cv2.resize(im, dsize=im_draw_size)  # type: np.ndarray
        im = self.filters.apply(im)

        Gdk.cairo_set_source_pixbuf(cr, pixbuf_from_array(im), *im_draw_offset)
        cr.paint()

    def _handle_preview_on_changed(self) -> None:
        self._buffer = self.preview.buffer

        self.queue_draw()
