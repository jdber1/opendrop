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
