import math
from typing import Sequence, Tuple

import cv2
import numpy as np

from opendrop.utility.geometry import Vector2


# Classes

class ContactAngle:
    # Fraction (of total contour length) of the drop contour to sample from ends to use to estimate contact angle.
    _SAMPLE_FRACTION = 0.025

    class NotEnoughDropPoints(Exception):
        pass

    def __init__(self, drop_profile: np.ndarray, surface: np.poly1d) -> None:
        self._drop_profile = drop_profile
        self._surface = surface

        self.left_tangent, self.left_angle, self.left_point \
            = (np.poly1d((math.nan, math.nan)), math.nan, Vector2(math.nan, math.nan))

        self.right_tangent, self.right_angle, self.right_point \
            = (np.poly1d((math.nan, math.nan)), math.nan, Vector2(math.nan, math.nan))

        self._calculate()

    def _calculate(self) -> None:
        drop_profile = np.copy(self._drop_profile)
        surface = self._surface

        surface_angle = math.atan(surface.c[0]) if len(surface.c) > 1 else 0

        rot_mtx = np.array([[math.cos(surface_angle), -math.sin(surface_angle)],
                            [math.sin(surface_angle),  math.cos(surface_angle)]])

        # Transform drop profile to coordinates where surface line is y=0
        drop_profile = drop_profile.astype(float)
        drop_profile[:, 1] -= surface.c[-1]

        drop_profile = (rot_mtx.T @ drop_profile.T).T
        drop_profile = drop_profile.astype(int)

        self._right_segment, self.right_tangent, self.right_angle, self.right_point \
            = self._calculate_right_params(drop_profile)

        # Mirror the contour left-to-right
        drop_profile = np.flipud(drop_profile)
        drop_profile[:, 0] *= -1

        self._left_segment, self.left_tangent, self.left_angle, self.left_point \
            = self._calculate_right_params(drop_profile)

        # Mirror back tangent and contact point.
        self.left_tangent = np.poly1d(self.left_tangent.coefficients * [-1, 1])
        self.left_point = Vector2(-self.left_point.x, self.left_point.y)
        self._left_segment = self._left_segment * [-1, 1]

        # Transform back to given coordinates.
        self._left_segment = (rot_mtx @ self._left_segment.T).T
        self._left_segment[:, 1] += surface.c[-1]
        self._left_segment = self._left_segment.astype(int)

        self._right_segment = (rot_mtx @ self._right_segment.T).T
        self._right_segment[:, 1] += surface.c[-1]
        self._right_segment = self._right_segment.astype(int)

        self.left_tangent = _transform_line(self.left_tangent, rot_mtx)
        self.left_tangent += surface.c[-1]
        self.left_point = Vector2(*(rot_mtx @ self.left_point))
        self.left_point += (0, surface.c[-1])

        self.right_tangent = _transform_line(self.right_tangent, rot_mtx)
        self.right_tangent += surface.c[-1]
        self.right_point = Vector2(*(rot_mtx @ self.right_point))
        self.right_point += (0, surface.c[-1])

    def _calculate_right_params(self, drop_profile: np.ndarray) -> Tuple[np.ndarray, np.poly1d, float, Vector2[float]]:
        try:
            right_segment, right_tangent = self._calculate_right_contact_tangent(drop_profile)
        except self.NotEnoughDropPoints:
            return (np.empty((0, 2)), np.poly1d((math.nan, math.nan)), math.nan, Vector2(math.nan, math.nan))

        return (
            right_segment,
            right_tangent,
            self._calculate_right_contact_angle(right_tangent),
            self._calculate_right_contact_point(right_tangent)
        )

    def _calculate_right_contact_tangent(self, drop_profile: np.ndarray) -> Tuple[np.ndarray, np.poly1d]:
        # Ignore points below the surface
        drop_profile = drop_profile[drop_profile[:, 1] >= 0]
        if len(drop_profile) == 0:
            raise self.NotEnoughDropPoints('Insufficient drop profile points')

        drop_contour_length = cv2.arcLength(drop_profile, closed=False)

        # Extract two halves of the contour.
        half_mask = _subarc_of_curve_mask(drop_profile, length=0.5 * drop_contour_length)
        half0 = drop_profile[half_mask]
        half1 = drop_profile[~half_mask]

        # And pick the half with the most right points.
        if np.average(half0, axis=0)[0] > np.average(half1, axis=0)[0]:
            half = half0
        else:
            half = half1

        # Sort the points from lowest to highest, assuming that near the contact point, the points along the drop
        # monotonically increase in height.
        half = half[np.argsort(half[:, 1])]

        # Extract a fraction of the first few points to approximate the tangent.
        right_segment = half[_subarc_of_curve_mask(half, length=self._SAMPLE_FRACTION * drop_contour_length)]

        # Fit a polynomial (of degree 1) to the first few points.
        right_fit = np.poly1d(np.polyfit(*right_segment.T, deg=1))

        # Get the line, tangent to the fit, at the lowest point of the extracted contour.
        right_contact_tangent = _get_tangent(right_fit, right_segment[0][0])

        return right_segment, right_contact_tangent

    def _calculate_right_contact_angle(self, right_contact_tangent: np.poly1d) -> float:
        tangent_gradient = right_contact_tangent.c[0] if len(right_contact_tangent.c) > 1 else 0

        right_contact_angle = math.atan2(abs(tangent_gradient), math.copysign(1, tangent_gradient))
        return right_contact_angle

    def _calculate_right_contact_point(self, right_contact_tangent: np.poly1d) -> Vector2[float]:
        roots = right_contact_tangent.roots
        if not roots:
            return Vector2(math.nan, math.nan)

        return Vector2(roots[0], right_contact_tangent(roots[0]))


# Helper functions

def _subarc_of_curve_mask(curve: np.ndarray, length: float) -> np.ndarray:
    mask = np.zeros(len(curve), dtype=bool)
    if len(curve) == 0:
        return mask
    elif len(curve) == 1:
        mask[0] = True
        return mask

    idx = [0, 1]

    while cv2.arcLength(curve[idx], closed=False) < length:
        if len(idx) >= len(curve):
            break

        idx.append(len(idx))

    mask[idx] = True

    return mask


def _get_tangent(poly: np.poly1d, x: float) -> np.poly1d:
    """Return the tangent of poly at x.
    """
    gradient = poly.deriv()(x)
    return np.poly1d((
        gradient,
        poly(x) - x * gradient
    ))


def _ensure_one_contour(drop_contours: Sequence[np.ndarray]) -> np.ndarray:
    """If len(drop_contours) == 0, return drop_contours[0], else, drop_contours must contain the left and right side
    of a drop attached to a needle, return a merged contour such that the first point is the left end of the drop and
    the last point is the right end.
    """
    if len(drop_contours) == 1:
        return drop_contours[0]

    contour0 = drop_contours[0]

    # If the first point is higher than the last point, reverse the order, so the first point is always the lowest.
    if contour0[0][1] < contour0[-1][1]:
        contour0 = np.flipud(contour0)

    contour1 = drop_contours[1]

    candidate_a = np.vstack((contour0, contour1))
    candidate_b = np.vstack((contour0, np.flipud(contour1)))

    if cv2.arcLength(candidate_a, closed=False) < cv2.arcLength(candidate_b, closed=False):
        drop_contour = candidate_a
    else:
        drop_contour = candidate_b

    # If the first point is to the right of the last point, reverse the order, so the first point is always to the
    # left, or in other words, ensure the drop contour goes from left to right.
    if drop_contour[0][0] > drop_contour[-1][0]:
        drop_contour = np.flipud(drop_contour)

    return drop_contour


def _transform_line(line: np.poly1d, transform_mtx: np.ndarray) -> np.poly1d:
    if not np.isfinite(line.coefficients).all():
        return line

    p0, p1 = (0, line(0)), (1, line(1))
    p0, p1 = (transform_mtx @ [*zip(p0, p1)]).T
    return np.poly1d(np.polyfit(*zip(p0, p1), deg=1))
