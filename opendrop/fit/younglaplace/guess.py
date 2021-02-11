import math
from typing import Tuple

import numpy as np

from ..pendant import find_pendant_apex
from .types import YoungLaplaceParam


# Math constants.
PI = math.pi
NAN = math.nan


def young_laplace_guess(data: Tuple[np.ndarray, np.ndarray]) -> tuple:
    params = np.empty(len(YoungLaplaceParam))

    apex, radius, rotation = find_pendant_apex(data)

    r, z = np.array([[np.cos(rotation), -np.sin(rotation)],
                     [np.sin(rotation),  np.cos(rotation)]]) \
           @ data

    bond = _bond_selected_plane(r, z, radius)

    params[YoungLaplaceParam.BOND] = bond
    params[YoungLaplaceParam.RADIUS] = radius
    params[YoungLaplaceParam.APEX_X] = apex.x
    params[YoungLaplaceParam.APEX_Y] = apex.y
    params[YoungLaplaceParam.ROTATION] = rotation
    
    return params


def _bond_selected_plane(r: np.ndarray, z: np.ndarray, radius: float) -> float:
    """Estimate Bond number by method of selected plane."""
    z_ix = np.argsort(z)
    if np.searchsorted(z, 2.0*radius, sorter=z_ix) < len(z):
        lower, upper = np.searchsorted(z, [1.95*radius, 2.05*radius], sorter=z_ix)
        radii = np.abs(r[lower:upper+1])
        r = radii.mean()/radius
        bond = 0.1756 * r**2 + 0.5234 * r**3 - 0.2563 * r**4
    else:
        bond = 0.15

    return bond


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
