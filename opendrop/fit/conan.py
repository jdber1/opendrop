import math
from typing import NamedTuple, Optional

import numpy as np

from opendrop.geometry import Line2, Vector2
from opendrop.utility.misc import rotation_mat2d
from opendrop.fit import line_fit, circle_fit


__all__ = ('ContactAngleFitResult', 'contact_angle_fit')

# Math constants
PI = math.pi
NAN = math.nan


class ContactAngleFitResult(NamedTuple):
    left_contact: Optional[Vector2[float]]
    right_contact: Optional[Vector2[float]]

    left_angle: Optional[float]
    right_angle: Optional[float]

    left_curvature: Optional[float]
    right_curvature: Optional[float]

    left_arc_center: Optional[Vector2[float]]
    right_arc_center: Optional[Vector2[float]]

    left_arclengths: Optional[np.ndarray]
    right_arclengths: Optional[np.ndarray]

    left_residuals: Optional[np.ndarray]
    right_residuals: Optional[np.ndarray]

    left_mask: Optional[np.ndarray]
    right_mask: Optional[np.ndarray]


def contact_angle_fit(data: np.ndarray, baseline: Line2) -> ContactAngleFitResult:
    # Drop points in (x, y) image coordinates.
    xy = data

    # Rotation matrix to transform to "baseline" coordinates.
    Q = np.array([baseline.unit, baseline.perp])

    # Drop points in (r, z) baseline coordinates.
    rz = Q @ (xy - np.reshape(baseline.pt0, (2, 1)))

    if abs(rz[1].min()) > abs(rz[1].max()):
        # Drop is probably on the other side of the line.
        Q[1] *= -1
        rz[1] *= -1

    # Sort in ascending height from baseline.
    z_ix = rz[1].argsort()
    z_ix_inv = z_ix.argsort()

    rz = rz[:, z_ix]
    xy = xy[:, z_ix]

    rc = rz[0].mean()

    left_mask  = rz[0] < rc
    right_mask = ~left_mask

    left_rz  = rz[:, left_mask]
    right_rz = rz[:, right_mask]
    
    # Approximates for left and right contact points.
    left_contact_rz  = left_rz[:, 0]
    right_contact_rz = right_rz[:, 0]

    left_dists = np.linalg.norm(left_rz - np.reshape(left_contact_rz, (2, 1)), axis=0)
    right_dists = np.linalg.norm(right_rz - np.reshape(right_contact_rz, (2, 1)), axis=0)

    base_width = right_contact_rz[0] - left_contact_rz[0]

    # Fit an arc to points near the contact using base_width as a distance scale.
    left_mask[left_mask]   &= left_dists  < 0.25 * base_width
    right_mask[right_mask] &= right_dists < 0.25 * base_width
    left_rz  = rz[:, left_mask]
    right_rz = rz[:, right_mask]

    left_angle = None
    left_contact_xy = None
    left_curvature = None
    left_arc_center_xy = None
    left_arclengths = None
    left_residuals = None
    right_angle = None
    right_contact_xy = None
    right_curvature = None
    right_arc_center_xy = None
    right_arclengths = None
    right_residuals = None

    left_arc_fit = _arc_fit(left_rz)
    right_arc_fit = _arc_fit(right_rz)

    if left_arc_fit is not None:
        left_angle = left_arc_fit.angle
        if left_arc_fit.contact is not None:
            left_contact_xy = Vector2(Q.T @ [left_arc_fit.contact, 0] + baseline.pt0)
        else:
            # Use initial guess.
            left_contact_xy = Vector2(Q.T @ left_contact_rz + baseline.pt0)
        left_curvature = left_arc_fit.curvature
        if left_arc_fit.arc_center is not None:
            left_arc_center_xy = Vector2(Q.T @ left_arc_fit.arc_center + baseline.pt0)
        left_arclengths = left_arc_fit.arclengths
        left_residuals = left_arc_fit.residuals

    if right_arc_fit is not None:
        if right_arc_fit.angle is not None:
            right_angle = PI - right_arc_fit.angle
        if right_arc_fit.contact is not None:
            right_contact_xy = Vector2(Q.T @ [right_arc_fit.contact, 0] + baseline.pt0)
        else:
            # Use initial guess.
            right_contact_xy = Vector2(Q.T @ right_contact_rz + baseline.pt0)
        right_curvature = right_arc_fit.curvature
        if right_arc_fit.arc_center is not None:
            right_arc_center_xy = Vector2(Q.T @ right_arc_fit.arc_center + baseline.pt0)
        right_arclengths = right_arc_fit.arclengths
        right_residuals = right_arc_fit.residuals

    return ContactAngleFitResult(
        left_contact_xy,
        right_contact_xy,
        left_angle,
        right_angle,
        left_curvature,
        right_curvature,
        left_arc_center_xy,
        right_arc_center_xy,
        left_arclengths,
        right_arclengths,
        left_residuals,
        right_residuals,
        left_mask[z_ix_inv],
        right_mask[z_ix_inv],
    )


class _ArcFitResult(NamedTuple):
    contact: Optional[Vector2[float]]
    angle: Optional[float]
    curvature: Optional[float]
    arc_center: Optional[Vector2[float]]
    arclengths: np.ndarray
    residuals: np.ndarray


def _arc_fit(data: np.ndarray) -> Optional[_ArcFitResult]:
    line_fit_result = line_fit(data)
    if line_fit_result is None:
        # A simple line fit somehow failed, this does not bode well.
        return None

    if not (line_fit_result.residuals < 1.0).all():
        circular_fit_result = _arc_circular_fit(data)
        if circular_fit_result is not None:
            return circular_fit_result

    curvature = 0.0
    arc_center = None
    angle = line_fit_result.angle
    angle %= PI

    # Arbitrary point on line of best fit.
    pt = rotation_mat2d(angle) @ [0, line_fit_result.rho]
    unit = Vector2(np.cos(angle), np.sin(angle))
    if not np.isclose(unit.y, 0):
        grad = unit.x/unit.y
        contact = pt[0] - grad * pt[1]
    else:
        # Line of best fit and baseline are roughly parallel, can't determine contact point.
        contact = None

    arclengths = unit @ (data - [[contact], [0]])
    residuals = line_fit_result.residuals

    return _ArcFitResult(
        contact,
        angle,
        curvature,
        arc_center,
        arclengths,
        residuals,
    )


def _arc_circular_fit(data: np.ndarray) -> Optional[_ArcFitResult]:
    circle_fit_result = circle_fit(data)
    if circle_fit_result is None:
        return None

    center = circle_fit_result.center
    radius = circle_fit_result.radius
    residuals = circle_fit_result.residuals
    if center.y > radius:
        # Make sure circle intersects the baseline, otherwise fallback to line fit.
        return None

    curvature = 1/radius

    l = np.sqrt(radius**2 - center.y**2)
    intersect1 = center.x - l
    intersect2 = center.x + l

    # Set contact point to be the intersection closest to the drop arc.
    if np.linalg.norm(data - [[intersect1], [0]], axis=0).min() \
            < np.linalg.norm(data - [[intersect2], [0]], axis=0).min():
        contact = intersect1
    else:
        contact = intersect2

    q = np.arctan2(center.y, center.x - contact)
    angle = (q + PI/2) % PI

    if center.x > contact:
        curvature *= -1
    elif center.x == contact:
        # In the unlikely event...
        if data[0].mean() > contact:
            curvature *= -1

    arclengths = np.arctan2(center.y - data[1], center.x - data[0]) - q
    if curvature < 0.0:
        arclengths *= -1

    ix = arclengths.argsort()
    arclengths = arclengths[ix]
    start = np.searchsorted(ix, 0.0, side='left')
    arclengths = np.roll(arclengths, -start)
    arclengths = np.unwrap(arclengths)
    arclengths %= 2*PI
    arclengths = np.roll(arclengths, start)
    arclengths = arclengths[ix.argsort()]
    arclengths *= radius

    return _ArcFitResult(
        contact,
        angle,
        curvature,
        center,
        arclengths,
        residuals,
    )
