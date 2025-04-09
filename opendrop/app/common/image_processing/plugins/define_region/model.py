# Copyright © 2020, Joseph Berry, Rico Tabor (opendrop.dev@gmail.com)
# OpenDrop is released under the GNU GPL License. You are free to
# modify and distribute the code, but always under the same license
#
# If you use this software in your research, please cite the following
# journal articles:
#
# J. D. Berry, M. J. Neeson, R. R. Dagastine, D. Y. C. Chan and
# R. F. Tabor, Measurement of surface and interfacial tension using
# pendant drop tensiometry. Journal of Colloid and Interface Science 454
# (2015) 226–237. https://doi.org/10.1016/j.jcis.2015.05.012
#
# E. Huang, T. Denning, A. Skoufis, J. Qi, R. R. Dagastine, R. F. Tabor
# and J. D. Berry, OpenDrop: Open-source software for pendant drop
# tensiometry & contact angle measurements, submitted to the Journal of
# Open Source Software
#
# These citations help us not only to understand who is using and
# developing OpenDrop, and for what purpose, but also to justify
# continued development of this code and other open source resources.
#
# OpenDrop is distributed WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.  You
# should have received a copy of the GNU General Public License along
# with this software.  If not, see <https://www.gnu.org/licenses/>.


from typing import Optional

from opendrop.utility.bindable.typing import Bindable
from opendrop.geometry import Rect2, Vector2
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
            pt0=start_pos,
            pt1=end_pos,
        ).map(int)

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
    def begin_define_pos(self) -> Optional[Vector2]:
        return self._begin_define_pos
