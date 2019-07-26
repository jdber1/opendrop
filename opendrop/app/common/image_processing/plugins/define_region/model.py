from typing import Optional

from opendrop.utility.bindable import Bindable
from opendrop.utility.geometry import Rect2, Vector2
from opendrop.utility.misc import clamp


class DefineRegionPluginModel:
    def __init__(self, in_region: Bindable[Rect2[int]], in_clip: Bindable[Optional[Rect2[int]]]) -> None:
        self.bn_region = in_region
        self._bn_clip = in_clip

        self._begin_define_pos = None

    def begin_define(self, begin_pos: Vector2[float]) -> None:
        assert not self.is_defining
        self._begin_define_pos = begin_pos

    def commit_define(self, end_pos: Vector2[float]) -> None:
        assert self.is_defining
        start_pos = self._begin_define_pos
        self._begin_define_pos = None

        region = Rect2(
            p0=start_pos,
            p1=end_pos,
        ).as_type(int)

        clip = self._bn_clip.get()

        if clip is not None:
            region = Rect2(
                x0=clamp(region.x0, clip.x0, clip.x1),
                y0=clamp(region.y0, clip.y0, clip.y1),
                x1=clamp(region.x1, clip.x0, clip.x1),
                y1=clamp(region.y1, clip.y0, clip.y1),
            )

        if region.w == 0 or region.h == 0:
            return

        self.bn_region.set(region)

    def discard_define(self) -> None:
        assert self.is_defining
        self._begin_define_pos = None

    @property
    def is_defining(self) -> bool:
        return self._begin_define_pos is not None

    @property
    def begin_define_pos(self) -> Vector2:
        return self._begin_define_pos
