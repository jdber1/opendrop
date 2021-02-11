import math
from typing import Tuple

import numpy as np
import scipy.optimize

from opendrop.geometry import Vector2


# Math constants.
PI = math.pi


__all__ = ('find_pendant_apex',)


def find_pendant_apex(data: Tuple[np.ndarray, np.ndarray]) -> tuple:
    x, y = data
    xc = x.mean()
    yc = y.mean()
    radius = np.hypot(x - xc, y - yc).mean()

    # Fit a circle to the most circular part of the data.
    ans = scipy.optimize.least_squares(
        _circle_residues,
        (xc, yc, radius),
        _circle_jac,
        args=(x, y),
        loss='cauchy',  # Ignore outliers.
        f_scale=radius/100,
        x_scale=(radius, radius, radius),
    )
    xc, yc, radius = ans.x
    resids = np.abs(ans.fun)
    resids_50ptile = np.quantile(resids, 0.5)

    # The somewhat circular-ish part of the drop profile.
    bowl_mask = resids < 10*resids_50ptile
    bowl_x = x[bowl_mask]
    bowl_y = y[bowl_mask]

    # Don't need these variables anymore.
    del resids, resids_50ptile

    # Find the symmetry axis of bowl.
    Ixx, Iyy, Ixy = _calculate_inertia(bowl_x, bowl_y)

    # Eigenvector calculation for a symmetric 2x2 matrix.
    rotation = 0.5 * np.arctan2(2 * Ixy, Ixx - Iyy)
    unit_r = np.array([ np.cos(rotation), np.sin(rotation)])
    unit_z = np.array([-np.sin(rotation), np.cos(rotation)])

    bowl_r = unit_r @ [bowl_x - xc, bowl_y - yc]
    bowl_z = unit_z @ [bowl_x - xc, bowl_y - yc]
    bowl_r_ix = np.argsort(bowl_r)
    bowl_z_ix = np.argsort(bowl_z)

    # Calculate "asymmetry" along each axis. We define this to be the squared difference between the left and
    # right points, integrated along the axis.
    ma_kernel = np.ones(len(bowl_r)//10)/(len(bowl_r)//10)
    asymm_r = (np.convolve((bowl_r - bowl_r.mean())[bowl_r_ix], ma_kernel, mode='valid')**2).sum()
    asymm_z = (np.convolve((bowl_z - bowl_z.mean())[bowl_z_ix], ma_kernel, mode='valid')**2).sum()
    if asymm_z > asymm_r:
        # Swap axes so z is the symmetry axis.
        rotation -= PI/2
        unit_r, unit_z = -unit_z, unit_r
        bowl_r, bowl_z = -bowl_z, bowl_r
        bowl_r_ix, bowl_z_ix = bowl_z_ix[::-1], bowl_r_ix

    # No longer useful variables (and potentially incorrect after axes swapping).
    del asymm_r, asymm_z

    bowl_z_hist, _ = np.histogram(bowl_z, bins=2 + len(bowl_z)//10)
    if bowl_z_hist.argmax() > len(bowl_z_hist)/2:
        # Rotate by 180 degrees since points are accumulating (where dz/ds ~ 0) at high z, i.e. drop apex is
        # not on the bottom.
        rotation += PI
        unit_r *= -1
        unit_z *= -1
        bowl_r *= -1
        bowl_z *= -1
        bowl_r_ix = bowl_r_ix[::-1]
        bowl_z_ix = bowl_z_ix[::-1]

    bowl_z_ix_apex_arc_stop = np.searchsorted(np.abs(bowl_r), 0.3*radius, side='right', sorter=bowl_z_ix)
    apex_arc_ix = bowl_z_ix[:bowl_z_ix_apex_arc_stop]
    apex_arc_x = bowl_x[apex_arc_ix]
    apex_arc_y = bowl_y[apex_arc_ix]

    if len(apex_arc_ix) > 10:
        # Fit another circle to a smaller arc around the apex. Points within 0.3 radians of the apex should
        # have roughly constant curvature across typical Bond values.
        ans = scipy.optimize.least_squares(
            _circle_residues,
            (xc, yc, radius),
            _circle_jac,
            args=(apex_arc_x, apex_arc_y),
            method='lm',  # Use fast MINPACK implementation.
            x_scale=(radius, radius, radius),
        )
        xc, yc, radius = ans.x

    apex_x, apex_y = [xc, yc] - radius * unit_z

    # Restrict rotation to [-pi, pi].
    rotation = (rotation + PI) % (2*PI) - PI

    return Vector2(apex_x, apex_y), radius, rotation


def _calculate_inertia(x: np.ndarray, y: np.ndarray) -> Tuple[float, float, float]:
    x = x - x.mean()
    y = y - y.mean()
    
    Ixx = (y**2).sum()
    Iyy = (x**2).sum()
    Ixy = -(x @ y)
    
    return Ixx, Iyy, Ixy


def _circle_residues(params, x, y):
    xc, yc, radius = params
    r = np.hypot(x - xc, y - yc)
    return r - radius


def _circle_jac(params, x, y):
    jac = np.empty((len(x), 3))

    xc, yc, radius = params
    dist_x = x - xc
    dist_y = y - yc
    r = np.hypot(dist_x, dist_y)

    jac[:, 0] = -dist_x/r
    jac[:, 1] = -dist_y/r
    jac[:, 2] = -1

    return jac
