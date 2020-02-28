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
import math
from typing import Optional

import numpy as np

from opendrop.processing.conan import ContactAngle
from opendrop.utility.bindable import BoxBindable, Bindable
from opendrop.utility.geometry import Line2, Vector2
from .features import FeatureExtractor


class ContactAngleCalculatorParams:
    def __init__(self) -> None:
        self.bn_surface_line_px = BoxBindable(None)  # type: Bindable[Optional[Line2]]


class ContactAngleCalculator:
    def __init__(self, features: FeatureExtractor, params: ContactAngleCalculatorParams) -> None:
        self._features = features
        self.params = params

        self.bn_left_tangent = BoxBindable(np.poly1d((math.nan, math.nan)))
        self.bn_left_angle = BoxBindable(math.nan)
        self.bn_left_point = BoxBindable(Vector2(math.nan, math.nan))
        self.bn_right_tangent = BoxBindable(np.poly1d((math.nan, math.nan)))
        self.bn_right_angle = BoxBindable(math.nan)
        self.bn_right_point = BoxBindable(Vector2(math.nan, math.nan))

        # Recalculate when inputs change
        features.bn_drop_profile_px.on_changed.connect(self._recalculate)
        params.bn_surface_line_px.on_changed.connect(self._recalculate)

        self._recalculate()

    def _recalculate(self) -> None:
        features = self._features
        params = self.params

        drop_profile = features.bn_drop_profile_px.get()
        if drop_profile is None:
            return

        surface = params.bn_surface_line_px.get()
        if surface is None:
            return

        drop_profile = drop_profile.copy()
        surface_poly1d = np.poly1d((surface.gradient, surface.eval_at(x=0).y))

        # ContactAngle expects the coordinates of drop profile to be such that the surface has a lower y-coordinate than
        # the drop, so mirror the drop in y-direction. (Remember drop profile is in 'image coordinates', where
        # increasing y-coordinate is 'downwards')
        drop_profile[:, 1] *= -1
        surface_poly1d = -surface_poly1d

        conancalc = ContactAngle(drop_profile, surface_poly1d)

        # Mirror the tangents and contact points back to original coordinate system as well.
        left_tangent = -conancalc.left_tangent
        left_point = Vector2(x=conancalc.left_point.x, y=-conancalc.left_point.y)
        right_tangent = -conancalc.right_tangent
        right_point = Vector2(x=conancalc.right_point.x, y=-conancalc.right_point.y)

        self.bn_left_tangent.set(left_tangent)
        self.bn_left_angle.set(conancalc.left_angle)
        self.bn_left_point.set(left_point)
        self.bn_right_tangent.set(right_tangent)
        self.bn_right_angle.set(conancalc.right_angle)
        self.bn_right_point.set(right_point)
