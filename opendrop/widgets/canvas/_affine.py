import math
from typing import Iterator, Optional

import cairo
from gi.repository import Gdk, GObject

from ._artist import Artist, ArtistContainer, ArtistInvalidateHandler


__all__ = ('AffineFrameArtist',)


class AffineFrameArtist(Artist, ArtistContainer):
    _transform: cairo.Matrix
    _last_draw_transform = None  # type: Optional[cairo.Matrix]

    _window = None  # type: Optional[Gdk.Window]

    def __init__(self, **properties) -> None:
        self._transform = cairo.Matrix()

        self._children = Children(
            invalidate_handler=self._artist_invalidated
        )
        super().__init__(**properties)

    def _artist_invalidated(self, artist: Artist, region: Optional[cairo.Region]) -> None:
        if region is None:
            self.invalidate()
            return

        if self._last_draw_transform is None:
            self.invalidate()
            return

        xx, xy, yx, yy, x0, y0 = self._last_draw_transform

        if yx or xy:
            # XXX: Calculating invalidated region for skew/rotations not implemented.
            self.invalidate()
            return

        region = cairo.Region([
            cairo.RectangleInt(
                math.floor(x0 + xx*rect.x),
                math.floor(y0 + yy*rect.y),
                math.ceil(xx*rect.width),
                math.ceil(yy*rect.height),
            )
            for rect in map(region.get_rectangle, range(region.num_rectangles()))
        ])

        self.invalidate(region)

    def map(self, window: Gdk.Window) -> None:
        self._window = window
        for artist in self._children:
            artist.map(window)

    def unmap(self) -> None:
        self._window = None
        self._last_draw_transform = None
        for artist in self._children:
            artist.unmap()

    def draw(self, cr: cairo.Context) -> None:
        cr.transform(self._transform)

        for artist in self._children.iter():
            cr.save()
            artist.draw(cr)
            cr.restore()

        self._last_draw_transform = self._transform

    def add_artist(self, artist: Artist, *, z_index: int = 0) -> None:
        self._children.add(artist, z_index=z_index)
        if self._window is not None:
            artist.map(self._window)
        self.invalidate()

    def remove_artist(self, artist: Artist) -> None:
        if self._window is not None:
            artist.unmap()
        self._children.remove(artist)
        self.invalidate()

    @GObject.Property(type=float)
    def transform_xx(self) -> float:
        return self._transform.xx

    @transform_xx.setter
    def transform_xx(self, xx: float) -> None:
        self._transform.xx = xx
        self.invalidate()

    @GObject.Property(type=float)
    def transform_yx(self) -> float:
        return self._transform.yx

    @transform_yx.setter
    def transform_yx(self, yx: float) -> None:
        self._transform.yx = yx
        self.invalidate()

    @GObject.Property(type=float)
    def transform_xy(self) -> float:
        return self._transform.xy

    @transform_xy.setter
    def transform_xy(self, xy: float) -> None:
        self._transform.xy = xy
        self.invalidate()

    @GObject.Property(type=float)
    def transform_yy(self) -> float:
        return self._transform.yy

    @transform_yy.setter
    def transform_yy(self, yy: float) -> None:
        self._transform.yy = yy
        self.invalidate()

    @GObject.Property(type=float)
    def transform_x0(self) -> float:
        return self._transform.x0

    @transform_x0.setter
    def transform_x0(self, x0: float) -> None:
        self._transform.x0 = x0
        self.invalidate()

    @GObject.Property(type=float)
    def transform_y0(self) -> float:
        return self._transform.y0

    @transform_y0.setter
    def transform_y0(self, y0: float) -> None:
        self._transform.y0 = y0
        self.invalidate()


class Children:
    def __init__(self, invalidate_handler: ArtistInvalidateHandler) -> None:
        self._children = set()
        self._relations = dict()
        self._invalidate_handler = invalidate_handler

    def add(self, artist: Artist, **properties) -> None:
        assert artist not in self._children

        artist.set_invalidate_handler(self._invalidate_handler)

        self._children.add(artist)
        self._relations[artist] = ChildRelation(artist, **properties)

    def remove(self, artist: Artist) -> None:
        assert artist in self._children

        self._children.remove(artist)
        del self._relations[artist]

        artist.set_invalidate_handler(None)

    def get_z_index(self, artist: Artist) -> int:
        relation = self._relations[artist]
        return relation.z_index

    def set_z_index(self, artist: Artist, z_index: int) -> None:
        relation = self._relations[artist]
        relation.z_index = z_index

    def clear(self) -> None:
        for artist in self._children.copy():
            self.remove(artist)

    def iter(self, *, z_ordered: bool = False) -> Iterator[Artist]:
        if z_ordered:
            children = sorted(self._children, key=lambda child: self._relations[child].z_index)
        else:
            children = self._children

        for child in children:
            yield child

    def __iter__(self) -> Iterator[Artist]:
        return self.iter()


class ChildRelation:
    def __init__(self, artist: Artist, *, z_index: int) -> None:
        self.artist = artist
        self.z_index = z_index
