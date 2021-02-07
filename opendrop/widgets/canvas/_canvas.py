from enum import Enum
from typing import Optional, MutableMapping, Tuple

import cairo
from gi.repository import GObject, Gdk, Gtk

from ._affine import AffineFrameArtist
from ._artist import Artist, ArtistContainer


__all__ = ('Canvas', 'CanvasAlign', 'CanvasAttachment')


class CanvasAlign(Enum):
    FIT = 1
    CENTER = 2


class CanvasAttachment(Enum):
    CANVAS = 1
    FLOATING = 2
    WIDGET = 3 


class Canvas(Gtk.DrawingArea, Gtk.Scrollable, ArtistContainer):
    _MIN_SCALE = 0.01
    _MAX_SCALE = 100

    _viewport_position = (0, 0)

    _content_size = (0, 0)
    _scale = 1
    _align = CanvasAlign.FIT

    _hscroll_policy = Gtk.ScrollablePolicy.MINIMUM
    _vscroll_policy = Gtk.ScrollablePolicy.MINIMUM

    _ignore_adjustment_changes = False

    def __init__(self, **properties) -> None:
        self._canvas_artist = AffineFrameArtist()
        self._canvas_artist.set_invalidate_handler(self._artist_invalidated)

        self._floating_artist = AffineFrameArtist()
        self._floating_artist.set_invalidate_handler(self._artist_invalidated)

        self._widget_artist = AffineFrameArtist()
        self._widget_artist.set_invalidate_handler(self._artist_invalidated)

        self._attachments = {}

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
        if adjustment is not None:
            try:
                if self._get_adjustment(orientation) == adjustment:
                    return
            except AttributeError:
                pass

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
            viewport_size = self.get_allocation().width
            viewport_position = self._viewport_position[0]
            content_size = self._content_size[0]
        else:
            viewport_size = self.get_allocation().height
            viewport_position = self._viewport_position[1]
            content_size = self._content_size[1]

        adjustment = self._get_adjustment(orientation)

        lower = 0
        upper = int(self._scale * content_size)
        page_size = min(viewport_size, upper - lower)

        adjustment.configure(
            viewport_position,
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

        self._viewport_position = (self.hadjustment.props.value, self.vadjustment.props.value)
        self.queue_allocate()

    def set_content_size(self, width: int, height: int) -> None:
        self._content_size = (width, height)
        self.queue_resize()

    def get_scale(self) -> float:
        return self._scale

    def canvas_to_floating(self, x: float, y: float) -> Tuple[float, float]:
        return x*self._scale, y*self._scale

    def floating_to_canvas(self, x: float, y: float) -> Tuple[float, float]:
        return x/self._scale, y/self._scale

    def canvas_to_widget(self, x: float, y: float) -> Tuple[float, float]:
        return x*self._scale - self._viewport_position[0], y*self._scale - self._viewport_position[1]

    def widget_to_canvas(self, x: float, y: float) -> Tuple[float, float]:
        return (x + self._viewport_position[0])/self._scale, (y + self._viewport_position[1])/self._scale

    def zoom(self, scale: float, focus_x: Optional[float] = None, focus_y: Optional[float] = None) -> None:
        scale = max(min(scale, self._MAX_SCALE), self._MIN_SCALE)
        if focus_x is None:
            focus_x = self.get_allocation().width/2
        if focus_y is None:
            focus_y = self.get_allocation().height/2

        factor = scale/self._scale

        self._viewport_position = (
            (self._viewport_position[0] + focus_x) * factor - focus_x,
            (self._viewport_position[1] + focus_y) * factor - focus_y
        )
        self._scale = scale

        self.queue_resize()

    @GObject.Property
    def align(self) -> CanvasAlign:
        return self._align

    @align.setter
    def align(self, align: CanvasAlign) -> None:
        self._align = align
        self.queue_allocate()

    def get_preferred_width(self) -> Tuple[int, int]:
        content_width = self._content_size[0]
        scale = self._scale
        return int(scale * content_width), int(scale * content_width)

    def get_preferred_height_for_width(self) -> Tuple[int, int]:
        return self.get_preferred_height()

    def get_preferred_height(self) -> Tuple[int, int]:
        content_height = self._content_size[1]
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

        if self._content_size[0] == 0 or self._content_size[1] == 0:
            align = CanvasAlign.CENTER

        if align is CanvasAlign.FIT:
            self._update_transform_fit()
        elif align is CanvasAlign.CENTER:
            self._update_transform_center()
        else:
            raise RuntimeError("Bad align value, this should never happen.")

    def _update_transform_fit(self) -> None:
        allocation = self.get_allocation()
        content_area = self._content_size

        scale = self._scale

        xx = scale
        yy = scale

        gap_x = max(0, allocation.width - xx*content_area[0])
        gap_y = max(0, allocation.height - yy*content_area[1])

        gap_zoom = 1 + min(gap_x / (xx*content_area[0]), gap_y / (yy*content_area[1]))
        xx *= gap_zoom
        yy *= gap_zoom

        gap_x = allocation.width - xx*content_area[0]
        gap_y = allocation.height - yy*content_area[1]

        if gap_x >= 0:
            x0 = gap_x/2
        else:
            x0 = max(min(-self._viewport_position[0], 0), gap_x)

        if gap_y >= 0:
            y0 = gap_y/2
        else:
            y0 = max(min(-self._viewport_position[1], 0), gap_y)

        self._canvas_artist.transform_xx = xx
        self._canvas_artist.transform_yy = yy
        self._canvas_artist.transform_x0 = x0
        self._canvas_artist.transform_y0 = y0

        self._floating_artist.transform_x0 = x0
        self._floating_artist.transform_y0 = y0

        self._scale = xx
        self._viewport_position = (-x0, -y0)

    def _update_transform_center(self) -> None:
        allocation = self.get_allocation()
        content_area = self._content_size

        scale = self._scale

        xx = scale
        yy = scale

        gap_x = allocation.width - xx*content_area[0]
        gap_y = allocation.height - yy*content_area[1]

        if gap_x >= 0:
            x0 = gap_x/2
        else:
            x0 = max(min(-self._viewport_position[0], 0), gap_x)

        if gap_y >= 0:
            y0 = gap_y/2
        else:
            y0 = max(min(-self._viewport_position[1], 0), gap_y)

        self._canvas_artist.transform_xx = xx
        self._canvas_artist.transform_yy = yy
        self._canvas_artist.transform_x0 = x0
        self._canvas_artist.transform_y0 = y0

        self._floating_artist.transform_x0 = x0
        self._floating_artist.transform_y0 = y0

        self._scale = xx
        self._viewport_position = (-x0, -y0)

    def add_artist(
            self,
            artist: Artist,
            *,
            attach: CanvasAttachment = CanvasAttachment.CANVAS,
            **properties
    ) -> None:
        if artist in self._attachments:
            raise ValueError("Artist is already attached to this canvas")
        
        if attach is CanvasAttachment.CANVAS:
            self._attachments[artist] = attach
            self._canvas_artist.add_artist(artist, **properties)
        elif attach is CanvasAttachment.FLOATING:
            self._attachments[artist] = attach
            self._floating_artist.add_artist(artist, **properties)
        elif attach is CanvasAttachment.WIDGET:
            self._attachments[artist] = attach
            self._widget_artist.add_artist(artist, **properties)

    def remove_artist(self, artist: Artist) -> None:
        if artist not in self._attachments:
            raise ValueError("Artist is not attached to this canvas")

        attach = self._attachments[artist]

        if attach is CanvasAttachment.CANVAS:
            self._canvas_artist.remove_artist(artist)
        elif attach is CanvasAttachment.FLOATING:
            self._floating_artist.remove_artist(artist)
        elif attach is CanvasAttachment.WIDGET:
            self._widget_artist.remove_artist(artist)

        del self._attachments[artist]

    def do_map(self) -> None:
        Gtk.DrawingArea.do_map.invoke(Gtk.DrawingArea, self)
        window = self.get_window()
        assert window is not None
        self._canvas_artist.map(window)

    def do_unmap(self) -> None:
        self._canvas_artist.unmap()
        Gtk.DrawingArea.do_unmap.invoke(Gtk.DrawingArea, self)

    def do_draw(self, cr: cairo.Context) -> None:
        cr.save()
        self._canvas_artist.draw(cr)
        cr.restore()

        cr.save()
        self._floating_artist.draw(cr)
        cr.restore()

        cr.save()
        self._widget_artist.draw(cr)
        cr.restore()

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
