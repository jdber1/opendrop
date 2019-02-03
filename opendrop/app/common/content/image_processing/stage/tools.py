from typing import Optional

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
