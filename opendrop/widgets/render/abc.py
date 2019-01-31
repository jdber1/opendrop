from abc import abstractmethod
from typing import Optional

import cairo
from gi.repository import GObject

from . import protocol
from .render import Render


class RenderObject(GObject.Object, protocol.RenderObject):
    def __init__(self, **options) -> None:
        super().__init__(**options)
        self._parent = None  # type: Optional[Render]

    def draw(self, cr: cairo.Context) -> None:
        assert self._parent is not None
        self._do_draw(cr)

    @abstractmethod
    def _do_draw(self, cr: cairo.Context) -> None:
        pass

    def set_parent(self, parent: Render) -> None:
        assert self._parent is None
        self._parent = parent

    def destroy(self) -> None:
        if self._parent is None:
            return
        self._parent.remove_render_object(self)

    @GObject.Signal
    def request_draw(self) -> None:
        """Let the parent know that this object needs to be redrawn."""
