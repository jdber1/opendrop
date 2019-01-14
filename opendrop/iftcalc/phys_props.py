import functools

import numpy as np
from scipy import integrate

from opendrop import sityping as si
from opendrop.iftcalc.younglaplace import de


# Memoize using a least-recently-used cache.
@functools.lru_cache()
def _calculate_vol_sur(size: float, bond_number: float) -> np.ndarray:
    # EPS = .000001 # need to use Bessel function Taylor expansion below
    x_vec_initial = [.000001, 0., 0., 0., 0.]

    return integrate.odeint(
        de.dataderiv, x_vec_initial, t=[0, size], args=(bond_number,)
    )[-1][-2:]  # type: np.ndarray


def calculate_ift(drop_density: si.Density, continuous_density: si.Density, bond_number: float, apex_radius: si.Length,
                  gravity: si.Acceleration) -> si.SurfaceTension:
    delta_density = abs(drop_density - continuous_density)  # type: si.Density
    gamma_ift = delta_density * gravity * apex_radius ** 2 / bond_number  # type: si.SurfaceTension

    return gamma_ift


def calculate_volume(profile_domain: float, bond_number: float, apex_radius: si.Length) -> si.Volume:
    return _calculate_vol_sur(profile_domain, bond_number)[0] * apex_radius ** 3


def calculate_surface_area(profile_domain: float, bond_number: float, apex_radius: si.Length) -> si.Area:
    return _calculate_vol_sur(profile_domain, bond_number)[1] * apex_radius ** 2


def calculate_worthington(drop_density: si.Density, continuous_density: si.Density, gravity: si.Acceleration,
                          ift: si.SurfaceTension, volume: si.Volume, needle_width: si.Length) -> float:
    delta_density = abs(drop_density - continuous_density)
    worthington_number = (delta_density * gravity * volume) / (np.pi * ift * needle_width)

    return worthington_number
