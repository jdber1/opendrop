from ._canvas import Canvas


class CanvasChart(Enum):
    CANVAS = 0
    VIEWPORT = 1


class InteractiveCanvas(Canvas):
    ...


class CanvasChildren:
    def __init__(self, invalidate_handler: ArtistInvalidateHandler) -> None:
        self._children = set()
        self._relations = dict()
        self._invalidate_handler = invalidate_handler

    def add(self, artist: Artist, **properties) -> None:
        assert artist not in self._children

        artist.set_invalidate_handler(self._invalidate_handler)

        self._children.add(artist)
        self._relations[artist] = CanvasChildRelation(artist, **properties)

    def remove(self, artist: Artist) -> None:
        assert artist in self._children

        self._children.remove(artist)
        del self._relations[artist]

        artist.set_invalidate_handler(None)

    def get_frame(self, artist: Artist) -> CanvasChart:
        relation = self._relations[artist]
        return relation.frame

    def clear(self) -> None:
        for artist in self._children.copy():
            self.remove(artist)

    def iter(self, *, frame: CanvasChart = None) -> Generator[Artist, None, None]:
        for child in self._children:
            relation = self._relations[child]
            if frame is not None and relation.frame != frame:
                continue
            yield child

    def __iter__(self) -> Iterator[Artist]:
        return self.iter()


class CanvasChildRelation:
    def __init__(self, artist: Artist, *, frame: CanvasChart) -> None:
        self.artist = artist
        self.frame = frame
