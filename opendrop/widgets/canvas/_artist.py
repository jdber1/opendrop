from typing import Any, Optional, Protocol

import cairo
from gi.repository import Gdk, GObject


class Artist(GObject.Object):
    def __init__(self, **properties) -> None:
        self._invalidate_handler = None  # type: Optional[ArtistInvalidateHandler]
        super().__init__(**properties)

    def map(self, window: Gdk.Window) -> None:
        """Called when owning Canvas is mapped or Artist is added to a mapped Canvas."""

    def unmap(self) -> None:
        """Called when owning Canvas is unmapped or Artist is removed from a mapped Canvas."""

    def draw(self, cr: cairo.Context) -> None:
        """Draw. The cairo context can be modified."""

    def invalidate_area(self, x: int, y: int, width: int, height: int) -> None:
        self.invalidate_region(cairo.Region(cairo.RectangleInt(x, y, width, height)))

    def invalidate_region(self, region: cairo.Region) -> None:
        if self._invalidate_handler is None: return
        self._invalidate_handler(self, region)

    def invalidate(self) -> None:
        if self._invalidate_handler is None: return
        self._invalidate_handler(self, None)

    def set_invalidate_handler(self, handler: 'Optional[ArtistInvalidateHandler]') -> None:
        self._invalidate_handler = handler


class ArtistContainer:
    def add_artist(self, artist: Artist, **properties) -> None:
        """Add 'artist' to container with optional child properties if applicable."""

    def remove_artist(self, artist: Artist) -> None:
        """Remove 'artist' from container."""


class ArtistInvalidateHandler(Protocol):
    def __call__(self, artist: Artist, region: Optional[cairo.Region]) -> Any: pass
