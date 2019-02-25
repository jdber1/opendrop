import math
from typing import Optional, Tuple

from opendrop.utility import keyboard
from opendrop.utility.bindable import AtomicBindable, AtomicBindableVar
from opendrop.utility.geometry import Vector2, Rect2, Line2
from opendrop.utility.misc import clamp
from .stage import StageTool


class RegionDragToDefine(StageTool):
    def __init__(self, canvas_size: Optional[Vector2]) -> None:
        self.bn_cursor_name = AtomicBindableVar('crosshair')

        self._canvas_size = canvas_size

        self.bn_selection = AtomicBindableVar(None)  # type: Optional[AtomicBindable[Rect2]]
        self.bn_selection_transient = AtomicBindableVar(None)  # type: Optional[AtomicBindable[Rect2]]
        self._drag_start = None  # type: Optional[Vector2[float]]

    def do_cursor_down(self, pos: Vector2[float]) -> None:
        pos = self._confine_to_canvas(pos)
        self._define_start(pos)

    def do_cursor_up(self, pos: Vector2[float]) -> None:
        if self._drag_start is None:
            return
        self._define_commit()

    def do_cursor_motion(self, pos: Vector2[float]) -> None:
        if self._drag_start is None:
            return
        pos = self._confine_to_canvas(pos)
        self._define_adjust(pos)

    def _define_start(self, pos: Vector2[float]) -> None:
        self._drag_start = pos
        self.bn_selection_transient.set(Rect2(p0=self._drag_start, p1=self._drag_start))

    def _define_commit(self) -> None:
        self._drag_start = None

        new_selection = self.bn_selection_transient.get()
        self.bn_selection_transient.set(None)

        if 0 in new_selection.size:
            return

        self.bn_selection.set(new_selection)

    def _define_adjust(self, pos: Vector2[float]) -> None:
        self.bn_selection_transient.set(Rect2(p0=self._drag_start, p1=pos))

    def _confine_to_canvas(self, pos: Vector2[float]) -> Vector2[float]:
        canvas_size = self._canvas_size
        if canvas_size is None:
            return pos

        return Vector2(clamp(pos.x, 0, canvas_size.x), clamp(pos.y, 0, canvas_size.y))


class LineDragToDefine(StageTool):
    def __init__(self, canvas_size: Optional[Vector2]) -> None:
        self.bn_cursor_name = AtomicBindableVar('crosshair')

        self._canvas_size = canvas_size

        self.bn_selection = AtomicBindableVar(None)  # type: Optional[AtomicBindable[Line2]]
        self.bn_selection_transient = AtomicBindableVar(None)  # type: Optional[AtomicBindable[Line2]]
        self._drag_start = None  # type: Optional[Vector2[float]]

    def do_cursor_down(self, pos: Vector2[float]) -> None:
        self._define_start(pos)

    def do_cursor_up(self, pos: Vector2[float]) -> None:
        if self._drag_start is None:
            return
        self._define_commit()

    def do_cursor_motion(self, pos: Vector2[float]) -> None:
        if self._drag_start is None:
            return
        self._define_adjust(pos)

    def do_keyboard_key_press(self, event: keyboard.KeyEvent) -> None:
        if self.bn_selection is None:
            return

        if self._drag_start is not None:
            # User is currently using mouse to define
            return

        if event.key is keyboard.Key.Up:
            self._nudge_selection_up()
        elif event.key is keyboard.Key.Down:
            self._nudge_selection_down()
        elif event.key is keyboard.Key.Left:
            self._nudgerot_selection_anticlockwise()
        elif event.key is keyboard.Key.Right:
            self._nudgerot_selection_clockwise()
        else:
            return

    def _nudge_selection_up(self) -> None:
        # Smaller image y-coordinate is upwards
        self._nudge_selection((0, -1))

    def _nudge_selection_down(self) -> None:
        self._nudge_selection((0, 1))

    def _nudge_selection(self, delta: Tuple[float, float]) -> None:
        line = self.bn_selection.get()
        if line is None:
            return

        new_line = Line2(p0=line.p0 + delta,
                         p1=line.p1 + delta)

        self.bn_selection.set(new_line)

    def _nudgerot_selection_clockwise(self) -> None:
        self._nudgerot_selection(-0.001)

    def _nudgerot_selection_anticlockwise(self) -> None:
        self._nudgerot_selection(0.001)

    def _nudgerot_selection(self, delta: float) -> None:
        """Rotate the currently selected line anticlockwise by `delta` radians."""
        line = self.bn_selection.get()
        if line is None:
            return

        canvas_size = self._canvas_size
        if canvas_size is not None:
            center_x = canvas_size.x/2
        else:
            center_x = line.p0.x

        line_angle = math.atan(line.gradient)
        new_line_angle = line_angle - delta

        new_p0 = line.eval_at(x=center_x)
        new_p1 = new_p0 + (math.cos(new_line_angle), math.sin(new_line_angle))

        new_line = Line2(p0=new_p0, p1=new_p1)

        self.bn_selection.set(new_line)

    def _define_start(self, pos: Vector2[float]) -> None:
        self._drag_start = pos
        self.bn_selection_transient.set(Line2(p0=self._drag_start, p1=self._drag_start))

    def _define_commit(self) -> None:
        self._drag_start = None

        new_selection = self.bn_selection_transient.get()
        self.bn_selection_transient.set(None)

        if new_selection.p0 == new_selection.p1:
            return

        self.bn_selection.set(new_selection)

    def _define_adjust(self, pos: Vector2[float]) -> None:
        self.bn_selection_transient.set(Line2(p0=self._drag_start, p1=pos))
