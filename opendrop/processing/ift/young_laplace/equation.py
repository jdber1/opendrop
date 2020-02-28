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


from math import sin, cos, pi
from typing import Union, Iterable, Tuple

import numpy as np
from scipy import (
    integrate as sp_integrate,
    interpolate as sp_interpolate
)


# noinspection NonAsciiCharacters
class YoungLaplaceSolution:
    INITIAL_SIZE = 4.0
    NUM_BREAKPOINTS = 5000

    def __init__(self, bond_number: float, apex_radius: float) -> None:
        self._bond_number = bond_number
        self._apex_radius = apex_radius

        self._solution_cache = self._solve(bond_number=bond_number, size=self.INITIAL_SIZE)

    @staticmethod
    def _solve(bond_number: float, size: float, num_breakpoints: int = NUM_BREAKPOINTS) -> sp_interpolate.PPoly:
        domain = np.linspace(start=0, stop=size, num=num_breakpoints)

        # EPS = .000001 # need to use Bessel function Taylor expansion below
        initial = [.000001, 0., 0., 0., 0., 0.]

        calculated = sp_integrate.odeint(ylderiv, initial, domain, args=(bond_number,))

        # Boundary conditions for the spline
        bc = ((1, ylderiv(calculated[0], 0, bond_number)),
              (1, ylderiv(calculated[-1], 0, bond_number)))

        # todo: make sure data is all finite

        return sp_interpolate.CubicSpline(
            x=domain, y=calculated, bc_type=bc, extrapolate=False
        )

    def __call__(self, s: Union[float, Iterable[float]]) -> np.ndarray:
        return self.evaluate(s)

    # Evaluate solution at `s` (which can be one value or an array of values).
    def evaluate(self, s: Union[float, Iterable[float]]) -> np.ndarray:
        try:
            iter(s)
        except TypeError:
            return self.evaluate([s])[0]

        s = np.array(s)

        if len(s) == 0:
            return np.empty((0, 6))

        # If the profile is evaluated outside of the interpolated region, expand it by 20%.
        if max(s) > self._solved_region_size:
            self._expand_solved_region(factor=1.2)

        data = self._solution_cache(abs(s))

        # Flip signs of appropriate quantities for negative `s` values queried.
        data[np.argwhere(s < 0), [0, 2, 3, 5]] *= -1
        data[:, [0, 1, 3, 4]] *= self._apex_radius

        return data

    def _expand_solved_region(self, factor: float) -> None:
        new_size = self._solved_region_size * factor
        self._solution_cache = self._solve(self._bond_number, size=new_size)

    @property
    def _solved_region_size(self) -> float:
        return self._solution_cache.x.max()

    def closest(self, p: Tuple[float, float], s_0: float, max_steps: int, tol: float) \
            -> Tuple[float, Tuple[float, float], bool]:
        r, z = p

        apex_radius = self._apex_radius
        bond_number = self._bond_number

        steps_exceeded = False
        flag_bump = 0

        s, e_r, e_z = s_0, 0, 0
        for step in range(max_steps):
            r_s, z_s, φ_s, dr_dB_s, dz_dB_s, dφ_dB_s = self.evaluate(s)

            e_r = r - r_s
            e_z = z - z_s

            dφ_ds = 2 - bond_number * (z_s/apex_radius) - sin(φ_s) / (r_s/apex_radius)

            s_next = s - self._f_Newton(e_r, e_z, φ_s, dφ_ds, apex_radius)

            if (s_next < 0 < r) or (r < 0 < s_next):  # Next parameter is on wrong side of profile
                s_next = 0
                flag_bump += 1

            if flag_bump >= 2:  # has already been pushed back twice - abort
                break

            if abs(s_next - s) < tol:
                break

            s = s_next
        else:
            steps_exceeded = True

        return s, (e_r, e_z), steps_exceeded

    # the function g(s) used in finding the arc length for the minimal distance
    @staticmethod
    def _f_Newton(e_r, e_z, φ, dφ_ds, apex_radius):
        f = - (e_r * cos(φ) + e_z * sin(φ)) / (apex_radius + dφ_ds * (e_r * sin(φ) - e_z * cos(φ)))
        return f


def calculate_volsur(bond_number: float, profile_size: float) -> Tuple[float, float]:
    # EPS = .000001 # need to use Bessel function Taylor expansion below
    x_vec_initial = [.000001, 0., 0., 0., 0.]

    return sp_integrate.odeint(
        dataderiv, x_vec_initial, t=[0, profile_size], args=(bond_number,)
    )[-1][-2:]


# minimise calls to sin() and cos()
# defines the Young--Laplace system of differential equations to be solved
# x_vec can be an array of vectors, in which case, ylderiv will calculate the derivative for each
# row in a for loop and return an np.ndarray of of the derivatives
def ylderiv(x_vec, t, bond_number):
    x, y, phi, x_Bond, y_Bond, phi_Bond = x_vec

    x_s = cos(phi)
    y_s = sin(phi)
    phi_s = 2 - bond_number * y - y_s/x
    x_Bond_s = - y_s * phi_Bond
    y_Bond_s = x_s * phi_Bond
    phi_Bond_s = y_s * x_Bond / (x**2) - x_s * phi_Bond / x - y - bond_number * y_Bond

    return [x_s, y_s, phi_s, x_Bond_s, y_Bond_s, phi_Bond_s]


# defines the Young--Laplace system of differential equations to be solved
def dataderiv(x_vec, t, bond_number):
    x, y, phi, vol, sur = x_vec

    x_s = cos(phi)
    y_s = sin(phi)
    phi_s = 2 - bond_number * y - sin(phi)/x
    vol_s = pi * x**2 * y_s
    sur_s = 2 * pi * x

    return [x_s, y_s, phi_s, vol_s, sur_s]
