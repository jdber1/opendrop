from typing import Tuple, Optional

import numpy as np

from opendrop.utility.misc import rotation_mat2d
from opendrop.features import find_pendant_apex

from .types import YoungLaplaceParam


def young_laplace_guess(data: Tuple[np.ndarray, np.ndarray]) -> Optional[tuple]:
    params = np.empty(len(YoungLaplaceParam))

    ans = find_pendant_apex(data)
    if ans is None:
        return None

    apex, radius, rotation = ans

    r, z = rotation_mat2d(-rotation) @ (data - np.reshape(apex, (2, 1))) 
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
        radii = np.abs(r[z_ix][lower:upper+1])
        x = radii.mean()/radius
        bond = max(0.10, 0.1756 * x**2 + 0.5234 * x**3 - 0.2563 * x**4)
    else:
        bond = 0.15

    return bond
