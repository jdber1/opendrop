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


import math
from typing import Optional, Tuple

from opendrop.utility.bindable.typing import Bindable
from opendrop.utility.geometry import Rect2, Vector2, Line2


class DefineLinePluginModel:
    def __init__(self, in_line: Bindable[Line2], in_clip: Bindable[Optional[Rect2[int]]]) -> None:
        self.bn_line = in_line
        self._bn_clip = in_clip

        self._begin_define_pos = None

    def begin_define(self, begin_pos: Vector2[float]) -> None:
        assert not self.is_defining
        self._begin_define_pos = begin_pos

    def commit_define(self, end_pos: Vector2[float]) -> None:
        assert self.is_defining
        start_pos = self._begin_define_pos
        self._begin_define_pos = None

        if start_pos == end_pos:
            return

        line = Line2(
            pt0=start_pos,
            pt1=end_pos,
        )

        self.bn_line.set(line)

    def discard_define(self) -> None:
        assert self.is_defining
        self._begin_define_pos = None

    @property
    def is_defining(self) -> bool:
        return self._begin_define_pos is not None

    @property
    def begin_define_pos(self) -> Optional[Vector2[float]]:
        return self._begin_define_pos

    def nudge_up(self) -> None:
        # Decreasing image y-coordinate is upwards
        self._nudge((0, -1))

    def nudge_down(self) -> None:
        self._nudge((0, 1))

    def _nudge(self, delta: Tuple[float, float]) -> None:
        line = self.bn_line.get()
        if line is None:
            return

        new_line = Line2(
            pt0=line.pt0 + delta,
            pt1=line.pt1 + delta
        )

        self.bn_line.set(new_line)

    def nudgerot_clockwise(self) -> None:
        self._nudgerot(-0.001)

    def nudgerot_anticlockwise(self) -> None:
        self._nudgerot(0.001)

    def _nudgerot(self, delta: float) -> None:
        """Rotate the currently selected line anticlockwise by `delta` radians.
        """
        line = self.bn_line.get()
        if line is None:
            return

        clip = self._bn_clip.get()
        if clip is not None:
            center_x = (clip.x0 + clip.x1)/2
        else:
            center_x = line.pt0.x

        line_angle = math.atan(line.gradient)
        new_line_angle = line_angle - delta

        new_p0 = line.eval(x=center_x)
        new_p1 = new_p0 + (math.cos(new_line_angle), math.sin(new_line_angle))

        new_line = Line2(pt0=new_p0, pt1=new_p1)

        self.bn_line.set(new_line)
