# Copyright © 2020, Joseph Berry, Rico Tabor (opendrop.dev@gmail.com)
# OpenDrop is released under the GNU GPL License. You are free to
# modify and distribute the code, but always under the same license
# (i.e. you cannot make commercial derivatives).
#
# If you use this software in your research, please cite the following
# journal articles:
#
# J. D. Berry, M. J. Neeson, R. R. Dagastine, D. Y. C. Chan and
# R. F. Tabor, Measurement of surface and interfacial tension using
# pendant drop tensiometry. Journal of Colloid and Interface Science 454
# (2015) 226–237. https://doi.org/10.1016/j.jcis.2015.05.012
#
#E. Huang, T. Denning, A. Skoufis, J. Qi, R. R. Dagastine, R. F. Tabor
#and J. D. Berry, OpenDrop: Open-source software for pendant drop
#tensiometry & contact angle measurements, submitted to the Journal of
# Open Source Software
#
#These citations help us not only to understand who is using and
#developing OpenDrop, and for what purpose, but also to justify
#continued development of this code and other open source resources.
#
# OpenDrop is distributed WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.  You
# should have received a copy of the GNU General Public License along
# with this software.  If not, see <https://www.gnu.org/licenses/>.
from typing import MutableSequence, Sequence

import cairo
from gi.repository import Gtk, GObject, Gdk

from opendrop.utility.cairomisc import cairo_saved
from opendrop.utility.geometry import Vector2, Rect2, Vector2Like
from . import protocol


class Render(Gtk.DrawingArea, protocol.Render):
    _canvas_size = Vector2(1, 1)
    _viewport_extents = Rect2(pos=(0, 0), size=_canvas_size)  # type: Rect2[float]
    _viewport_stretch = protocol.Render.ViewportStretch.FIT

    STYLE = """
        .render {
            border: 1px solid white;
        }
    """

    _STYLE_PROV = Gtk.CssProvider()
    _STYLE_PROV.load_from_data(bytes(STYLE, 'utf-8'))

    class RenderObjectContainer:
        def __init__(self, render_object: protocol.RenderObject, handler_ids: Sequence[int]) -> None:
            self.render_object = render_object
            self.handler_ids = tuple(handler_ids)

    def __init__(self, *, can_focus=True, **options) -> None:
        super().__init__(focus_on_click=True, can_focus=can_focus, **options)
        self._ro_containers = []  # type: MutableSequence[Render.RenderObjectContainer]

        self.add_events(
            Gdk.EventMask.POINTER_MOTION_MASK
            | Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.BUTTON_RELEASE_MASK
            | Gdk.EventMask.FOCUS_CHANGE_MASK
            | Gdk.EventMask.ENTER_NOTIFY_MASK
            | Gdk.EventMask.LEAVE_NOTIFY_MASK
            | Gdk.EventMask.KEY_PRESS_MASK)

        self.get_style_context().add_class('render')
        self.get_style_context().add_provider(self._STYLE_PROV, Gtk.STYLE_PROVIDER_PRIORITY_USER)

    def do_draw(self, cr: cairo.Context) -> None:
        viewport_widget_extents = self.props.viewport_widget_extents

        with cairo_saved(cr):
            cr.rectangle(*viewport_widget_extents.pos, *viewport_widget_extents.size)
            cr.clip()
            for ro in self._render_objects:
                ro.draw(cr)

        if self.has_focus():
            # Draw focus indicator
            stroke_width = 1
            rectangle_pos = viewport_widget_extents.pos + (stroke_width/2, stroke_width/2)
            rectangle_size = viewport_widget_extents.size - (stroke_width, stroke_width)
            cr.rectangle(*rectangle_pos, *rectangle_size)
            cr.set_source_rgb(70/255, 142/255, 220/255)
            cr.set_line_width(stroke_width)
            cr.stroke()

    @property
    def _render_objects(self) -> Sequence[protocol.RenderObject]:
        return sorted(
            (container.render_object for container in self._ro_containers),
            key=lambda ro: ro.props.z_index,
        )

    def add_render_object(self, ro: protocol.RenderObject) -> None:
        handler_ids = (
            ro.connect('request-draw', lambda _: self.queue_draw()),
        )
        self._ro_containers.append(self.RenderObjectContainer(
            render_object=ro,
            handler_ids=handler_ids))
        ro.set_parent(self)

        self.queue_draw()

    def remove_render_object(self, ro: protocol.RenderObject) -> None:
        container = self._ro_container_from_ro(ro)

        for handler_id in container.handler_ids:
            ro.disconnect(handler_id)
        self._ro_containers.remove(container)

        self.queue_draw()

    def _ro_container_from_ro(self, ro: protocol.RenderObject) -> 'Render.RenderObjectContainer':
        for container in self._ro_containers:
            if container.render_object is ro:
                return container
        else:
            raise ValueError('No container found for {}.'.format(ro))

    def do_button_press_event(self, event: Gdk.EventButton) -> None:
        self.emit('cursor-down-event', self._canvas_coord_from_widget(Vector2(event.x, event.y)))

        if self.props.can_focus:
            self.grab_focus()

    def do_button_release_event(self, event: Gdk.EventButton) -> None:
        self.emit('cursor-up-event', self._canvas_coord_from_widget(Vector2(event.x, event.y)))

    def do_motion_notify_event(self, event: Gdk.EventButton) -> None:
        self.emit('cursor-motion-event', self._canvas_coord_from_widget(Vector2(event.x, event.y)))

    def do_key_press_event(self, event: Gdk.EventKey) -> bool:
        if event.keyval == Gdk.KEY_Tab:
            # Allow user to use the tab key to cycle focus to another widget
            return False

        # Stop event propagation
        return True

    # Cursor signals

    @GObject.Signal(arg_types=(object,))
    def cursor_down_event(self, pos: Vector2[float]) -> None:
        pass

    @GObject.Signal(arg_types=(object,))
    def cursor_up_event(self, pos: Vector2[float]) -> None:
        pass

    @GObject.Signal(arg_types=(object,))
    def cursor_motion_event(self, pos: Vector2[float]) -> None:
        pass

    # Coordinate transform functions

    def _widget_coord_from_canvas(self, coord_canvas: Vector2Like[float]) -> Vector2[float]:
        coord_canvas = Vector2(*coord_canvas)

        viewport_extents = self.props.viewport_extents
        viewport_widget_extents = self.props.viewport_widget_extents

        coord_viewport = coord_canvas - viewport_extents.pos
        coord_viewport_pct = Vector2(coord_viewport.x / viewport_extents.size.x,
                                     coord_viewport.y / viewport_extents.size.y)
        coord_viewport_widget = Vector2(coord_viewport_pct.x * viewport_widget_extents.size.x,
                                        coord_viewport_pct.y * viewport_widget_extents.size.y)
        coord_widget = viewport_widget_extents.pos + coord_viewport_widget

        return coord_widget

    def _canvas_coord_from_widget(self, coord_widget: Vector2Like[float]) -> Vector2[float]:
        coord_widget = Vector2(*coord_widget)

        viewport_extents = self.props.viewport_extents
        viewport_widget_extents = self.props.viewport_widget_extents

        coord_viewport_widget = coord_widget - viewport_widget_extents.pos
        coord_viewport_pct = Vector2(coord_viewport_widget.x / viewport_widget_extents.size.x,
                                     coord_viewport_widget.y / viewport_widget_extents.size.y)
        coord_viewport = Vector2(coord_viewport_pct.x * viewport_extents.size.x,
                                 coord_viewport_pct.y * viewport_extents.size.y)
        coord_canvas = viewport_extents.pos + coord_viewport

        return coord_canvas

    def _widget_dist_from_canvas(self, dist_canvas: Vector2Like[float]) -> Vector2[float]:
        dist_canvas = Vector2(*dist_canvas)

        viewport_size = self.props.viewport_extents.size
        viewport_widget_size = self.props.viewport_widget_extents.size

        scale = Vector2(viewport_widget_size.x/viewport_size.x, viewport_widget_size.y/viewport_size.y)
        dist_widget = Vector2(scale.x * dist_canvas.x, scale.y * dist_canvas.y)

        return dist_widget

    def _canvas_dist_from_widget(self, dist_widget: Vector2Like[float]) -> Vector2[float]:
        dist_widget = Vector2(*dist_widget)

        viewport_size = self.props.viewport_extents.size
        viewport_widget_size = self.props.viewport_widget_extents.size

        scale = Vector2(viewport_size.x/viewport_widget_size.x, viewport_size.y/viewport_widget_size.y)
        dist_canvas = Vector2(scale.x * dist_widget.x, scale.y * dist_widget.y)

        return dist_canvas

    # Canvas geometry properties

    @GObject.Property
    def canvas_size(self) -> Vector2[float]:
        return self._canvas_size

    @canvas_size.setter
    def canvas_size(self, new_size: Vector2[float]) -> None:
        self._canvas_size = new_size
        self.queue_draw()

    @GObject.Property
    def viewport_extents(self) -> Rect2[float]:
        return self._viewport_extents

    @viewport_extents.setter
    def viewport_extents(self, new_extents: Rect2[float]) -> None:
        self._viewport_extents = new_extents
        self.queue_draw()

    @GObject.Property
    def viewport_widget_extents(self) -> Rect2[float]:
        return Rect2(pos=self._viewport_widget_pos, size=self._viewport_widget_size)

    @property
    def _viewport_widget_size(self) -> Vector2[float]:
        widget_size = Vector2(self.get_allocated_width(), self.get_allocated_height())
        return self._calculate_stretch_size(
            stretch=self._viewport_stretch,
            reference_size=widget_size,
            child_size=self._viewport_extents.size)

    @property
    def _viewport_widget_pos(self) -> Vector2[float]:
        widget_size = Vector2(self.get_allocated_width(), self.get_allocated_height())
        return self._calculate_offset_for_centred_rectangles(
            reference_size=widget_size,
            child_size=self._viewport_widget_size)

    @classmethod
    def _calculate_stretch_size(cls, stretch: protocol.Render.ViewportStretch, reference_size: Vector2[float],
                                child_size: Vector2[float]) -> Vector2[float]:
        reference_aspect = reference_size[0] / reference_size[1]
        child_aspect = child_size[0] / child_size[1]

        if stretch is cls.ViewportStretch.FILL and (reference_aspect > child_aspect) \
                or stretch is cls.ViewportStretch.FIT and (reference_aspect <= child_aspect):
            scale_factor = reference_size[0] / child_size[0]
        else:
            scale_factor = reference_size[1] / child_size[1]

        return child_size * scale_factor

    @staticmethod
    def _calculate_offset_for_centred_rectangles(reference_size: Vector2[float], child_size: Vector2[float]) \
            -> Vector2[float]:
        offset = reference_size / 2 - child_size / 2
        return offset
