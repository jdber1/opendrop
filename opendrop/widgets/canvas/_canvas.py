from enum import Enum
from typing import Optional, MutableMapping, Tuple

import cairo
from gi.repository import GObject, Gdk, Gtk

from opendrop.utility.geometry import Rect2

from ._affine import AffineFrameArtist
from ._artist import Artist, ArtistContainer


__all__ = ('Canvas', 'CanvasAlign')


class CanvasAlign(Enum):
    FIT = 1
    CENTER = 2


# add surface? here, CANVAS, BIN, VIEWPORT
# ::zoom signal

# TODO: handle when content_area is not at origin

class Canvas(Gtk.DrawingArea, Gtk.Scrollable, ArtistContainer):
    _scale_request = 1
    _scale = 1
    _viewport_origin = (0, 0)
    _content_area = Rect2(0, 0, 0, 0)

    _align = CanvasAlign.FIT

    _ignore_adjustment_changes = False

    _hscroll_policy = Gtk.ScrollablePolicy.MINIMUM
    _vscroll_policy = Gtk.ScrollablePolicy.MINIMUM

    def __init__(self, **properties) -> None:
        self._artist = AffineFrameArtist()
        self._artist.set_invalidate_handler(self._artist_invalidated)

        self._adjustments = {
            Gtk.Orientation.HORIZONTAL: None,
            Gtk.Orientation.VERTICAL: None,
        }  # type: MutableMapping[Gtk.Orientation, Optional[Gtk.Adjustment]]

        self._adjustment_handler_ids = {
            Gtk.Orientation.HORIZONTAL: None,
            Gtk.Orientation.VERTICAL: None,
        }  # type: MutableMapping[Gtk.Orientation, Optional[int]]

        super().__init__(**properties)

        self._default_adjustments_if_none()

    def _get_adjustment(self, orientation: Gtk.Orientation) -> Gtk.Adjustment:
        adjustment = self._adjustments[orientation]
        if adjustment is None:
            raise AttributeError
        return adjustment

    def _set_adjustment(
            self,
            orientation: Gtk.Orientation,
            adjustment: Optional[Gtk.Adjustment] = None
    ) -> None:
        if adjustment and self._get_adjustment(orientation) == adjustment:
            return

        self._disconnect_adjustment(orientation)

        new_adjustment = adjustment is None
        if new_adjustment:
            adjustment = Gtk.Adjustment()

        self._adjustments[orientation] = adjustment
        self._configure_adjustment(orientation)

        self._adjustment_handler_ids[orientation] \
            = adjustment.connect('value-changed', self._adjustment_value_changed)

        if not new_adjustment:
            self._adjustment_value_changed(adjustment)

    def _configure_adjustment(self, orientation: Gtk.Orientation) -> None:
        if orientation is Gtk.Orientation.HORIZONTAL:
            viewport_origin = self._viewport_origin[0]
            viewport_size = self.get_allocation().width
            content_size = self._content_area.width
        else:
            viewport_origin = self._viewport_origin[1]
            viewport_size = self.get_allocation().height
            content_size = self._content_area.height

        adjustment = self._get_adjustment(orientation)

        page_size = int(min(viewport_size, content_size * self._scale))
        lower = 0
        upper = int(content_size * self._scale)

        adjustment.configure(
            viewport_origin,
            lower,
            upper,
            page_size * 0.1,  # step_increment
            page_size * 0.9,  # page_increment
            page_size,  # page_size
        )

    def _disconnect_adjustment(self, orientation: Gtk.Orientation) -> None:
        adjustment = self._adjustments[orientation]
        if adjustment is None: return

        handler_id = self._adjustment_handler_ids[orientation]
        if handler_id is None: return

        adjustment.disconnect(handler_id)
        self._adjustment_handler_ids[orientation] = None

    def _default_adjustments_if_none(self) -> None:
        for orientation, adjustment in self._adjustments.items():
            if adjustment is None:
                self._set_adjustment(orientation)

    def _adjustment_value_changed(self, adjustment: Gtk.Adjustment) -> None:
        if self._ignore_adjustment_changes: return

        self._viewport_origin = (
            self.hadjustment.props.value,
            self.vadjustment.props.value,
        )
        self.queue_allocate()

    def set_content_area(self, x: int, y: int, width: int, height: int) -> None:
        self._content_area = Rect2(x=x, y=y, w=width, h=height)
        self.queue_resize()

    def get_scale(self) -> float:
        return self._scale

    def get_scale_request(self) -> float:
        return self._scale_request

    def zoom(self, scale: float, focus: Optional[Tuple[float, float]] = None) -> None:
        if focus is None:
            focus = self.get_allocation().width/2, self.get_allocation().height/2

        scale = max(min(scale, 100), 0.01)

        factor = scale/self._scale_request

        self._viewport_origin = (
            (self._viewport_origin[0] + focus[0]) * factor - focus[0],
            (self._viewport_origin[1] + focus[1]) * factor - focus[1]
        )

        self._scale_request = scale
        self.queue_resize()

    @GObject.Property
    def align(self) -> CanvasAlign:
        return self._align

    @align.setter
    def align(self, align: CanvasAlign) -> None:
        self._align = align
        self.queue_allocate()

    def get_preferred_width(self) -> Tuple[int, int]:
        content_width = self._content_area.width
        scale = self._scale
        return int(scale * content_width), int(scale * content_width)

    def get_preferred_height_for_width(self) -> Tuple[int, int]:
        return self.get_preferred_height()

    def get_preferred_height(self) -> Tuple[int, int]:
        content_height = self._content_area.height
        scale = self._scale
        return int(scale * content_height), int(scale * content_height)

    def get_preferred_width_for_height(self) -> Tuple[int, int]:
        return self.get_preferred_width()

    def do_size_allocate(self, allocation: Gdk.Rectangle) -> None:
        Gtk.DrawingArea.do_size_allocate.invoke(Gtk.DrawingArea, self, allocation)

        self._update_transform()

        try:
            self._ignore_adjustment_changes = True
            self._configure_adjustment(Gtk.Orientation.VERTICAL)
            self._configure_adjustment(Gtk.Orientation.HORIZONTAL)
        finally:
            self._ignore_adjustment_changes = False

    def _update_transform(self) -> None:
        align = self._align

        if self._content_area.width == 0 or self._content_area.height == 0:
            align = CanvasAlign.CENTER

        if align is CanvasAlign.FIT:
            self._update_transform_fit()
        elif align is CanvasAlign.CENTER:
            self._update_transform_center()
        else:
            raise RuntimeError("Bad align value, this should never happen.")

    def _update_transform_fit(self) -> None:
        allocation = self.get_allocation()
        content_area = self._content_area

        scale_request = self._scale_request

        xx = scale_request
        yy = scale_request

        gap_x = max(0, allocation.width - xx*content_area.width)
        gap_y = max(0, allocation.height - yy*content_area.height)

        gap_zoom = 1 + min(gap_x / (xx*content_area.width), gap_y / (yy*content_area.height))
        xx *= gap_zoom
        yy *= gap_zoom

        gap_x = allocation.width - xx*content_area.width
        gap_y = allocation.height - yy*content_area.height

        if gap_x >= 0:
            x0 = gap_x/2
        else:
            x0 = max(min(-self._viewport_origin[0], 0), gap_x)

        if gap_y >= 0:
            y0 = gap_y/2
        else:
            y0 = max(min(-self._viewport_origin[1], 0), gap_y)

        self._artist.transform_xx = xx
        self._artist.transform_yy = yy
        self._artist.transform_x0 = x0
        self._artist.transform_y0 = y0

        self._scale = xx
        self._viewport_origin = (-x0, -y0)

    def _update_transform_center(self) -> None:
        allocation = self.get_allocation()
        content_area = self._content_area

        scale_request = self._scale_request

        xx = scale_request
        yy = scale_request

        gap_x = allocation.width - scale_request*content_area.width
        gap_y = allocation.height - scale_request*content_area.height

        if gap_x >= 0:
            x0 = gap_x/2
        else:
            x0 = max(min(-self._viewport_origin[0], 0), gap_x)

        if gap_y >= 0:
            y0 = gap_y/2
        else:
            y0 = max(min(-self._viewport_origin[1], 0), gap_y)

        self._artist.transform_xx = xx
        self._artist.transform_yy = yy
        self._artist.transform_x0 = x0
        self._artist.transform_y0 = y0

        self._scale = xx
        self._viewport_origin = (-x0, -y0)

    def add_artist(self, artist: Artist, **properties) -> None:
        self._artist.add_artist(artist, **properties)

    def remove_artist(self, artist: Artist) -> None:
        self._artist.remove_artist(artist)

    def do_map(self) -> None:
        Gtk.DrawingArea.do_map.invoke(Gtk.DrawingArea, self)
        self._artist.map(self.get_window())

    def do_unmap(self) -> None:
        self._artist.unmap()
        Gtk.DrawingArea.do_unmap.invoke(Gtk.DrawingArea, self)

    def do_draw(self, cr: cairo.Context) -> None:
        self._artist.draw(cr)

    def _artist_invalidated(self, artist: Artist, region: Optional[cairo.Region]) -> None:
        if region is not None:
            self.queue_draw_region(region)
        else:
            self.queue_draw()

    @GObject.Property(type=Gtk.Adjustment)
    def hadjustment(self) -> Gtk.Adjustment:
        return self._get_adjustment(Gtk.Orientation.HORIZONTAL)

    @hadjustment.setter
    def hadjustment(self, adjustment: Gtk.Adjustment) -> None:
        self._set_adjustment(Gtk.Orientation.HORIZONTAL, adjustment)

    @GObject.Property(type=Gtk.Adjustment)
    def vadjustment(self) -> Gtk.Adjustment:
        return self._get_adjustment(Gtk.Orientation.VERTICAL)

    @vadjustment.setter
    def vadjustment(self, adjustment: Gtk.Adjustment) -> None:
        self._set_adjustment(Gtk.Orientation.VERTICAL, adjustment)

    @GObject.Property(type=Gtk.ScrollablePolicy, default=Gtk.ScrollablePolicy.MINIMUM)
    def hscroll_policy(self) -> Gtk.ScrollablePolicy:
        return self._hscroll_policy

    @hscroll_policy.setter
    def hscroll_policy(self, policy: Gtk.ScrollablePolicy) -> None:
        self._hscroll_policy = policy

    @GObject.Property(type=Gtk.ScrollablePolicy, default=Gtk.ScrollablePolicy.MINIMUM)
    def vscroll_policy(self) -> Gtk.ScrollablePolicy:
        return self._vscroll_policy

    @vscroll_policy.setter
    def vscroll_policy(self, policy: Gtk.ScrollablePolicy) -> None:
        self._vscroll_policy = policy
