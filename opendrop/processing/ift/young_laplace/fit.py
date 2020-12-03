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


import io
import itertools
import math
import traceback
from collections import namedtuple
from enum import IntEnum
from math import cos, sin
from typing import Optional, Tuple, Union, Iterable, overload, Any, Callable

import numpy as np

from . import best_guess
from . import equation
from . import tolerances

SLOW_CONVERGENCE_THRESHOLD = 0.25
FAST_CONVERGENCE_THRESHOLD = 0.75


# noinspection NonAsciiCharacters
class YoungLaplaceFit:
    _Params = namedtuple('Params', ('apex_x', 'apex_y', 'apex_radius', 'bond_number', 'rotation'))

    class _Cancelled(Exception):
        pass

    def __init__(self, drop_profile: np.ndarray, *,
                 on_update: Optional[Callable[['YoungLaplaceFit'], Any]] = None,
                 logger: Optional[Callable[[str], Any]] = None) -> None:

        self._src_profile = drop_profile[drop_profile[:, 1].argsort()]

        self._on_update = on_update or (lambda x: None)
        self._logger = logger or (lambda x: None)

        self._is_cancelled = False
        self._is_done = False

        self._cancel_flag = False

        self._params_ = self._Params(math.nan, math.nan, math.nan, math.nan, math.nan)

        self._volume = math.nan
        self._surface_area = math.nan

        self._apex_rot_matrix = np.identity(2)

        # The theoretical profile of the drop based on the current estimated parameters.
        self._profile = None  # type: Optional[equation.YoungLaplaceSolution]
        self._profile_size = 0.0
        self._residuals = np.empty((0, 2))

        self._fit()

    def _fit(self) -> None:
        # Guess the initial parameters
        self._initial_guess()

        # Optimise
        try:
            stop_reason = self._optimise()
        except self._Cancelled:
            self._is_cancelled = True
            self._logger('\nCancelled.\n')
        except Exception as exc:
            # Unexpected error occurred in the fitting routine.
            buffer = io.StringIO()
            traceback.print_exception(type(exc), exc, tb=exc.__traceback__, file=buffer)
            self._logger('\n{}'.format(buffer.getvalue()))
        else:
            self._logger('\nFitting finished ({})\n'.format(_StopReason.str_from_num(stop_reason)))

        self._is_done = True

        self._on_update(self)

    def _initial_guess(self) -> None:
        """Initialises parameters to a first best guess.
        """

        if (self._src_profile[0, 1] + self._src_profile[-1, 1])/2 < np.mean(self._src_profile[:, 1]):
            flipped = self._src_profile.copy()
            flipped[:, 1] *= -1
            flipped = flipped[::-1]
            apex_x, apex_y, apex_radius = best_guess.fit_circle(flipped)
            bond_number = best_guess.bond_number(flipped, apex_x, apex_y, apex_radius)
            apex_y *= -1
            rotation = math.pi
            self._src_profile = self._src_profile[::-1]
        else:
            apex_x, apex_y, apex_radius = best_guess.fit_circle(self._src_profile)
            bond_number = best_guess.bond_number(self._src_profile, apex_x, apex_y, apex_radius)
            rotation = 0.0

        self._params = self._Params(apex_x, apex_y, apex_radius, bond_number, rotation)

    def _optimise(self) -> '_StopReason':
        self._logger('{: >4}  {: >10}  {: >10}  {: >10}  {: >11}  {: >10}  {:>11}\n'.format(
            'Step', 'Objective', 'x-centre', 'z-centre', 'Apex radius', 'Bond', 'Image angle'
        ))

        λ = 0
        λ_cutoff = 0

        # Initialise sum of squared residuals to be arbitrarily large.
        ssr = math.inf

        for step in itertools.count():
            λ, λ_cutoff, ssr, stop_reason = self._optimise_step(λ, λ_cutoff, ssr)

            objective = ssr/self.degrees_of_freedom

            # Log the fitting progress
            self._logger(
                '{step: >4d} '
                '{objective: >11.4g} '
                '{apex_x: >11.4g} '
                '{apex_y: >11.4g} '
                '{apex_radius: >12.4g} '
                '{bond_number: >11.4g} '
                '{rotation: >11.4g}°\n'
                .format(
                    step=step,
                    objective=objective,
                    apex_x=self._params.apex_x,
                    apex_y=self._params.apex_y,
                    apex_radius=self._params.apex_radius,
                    bond_number=self._params.bond_number,
                    rotation=math.degrees(self.rotation),
                )
            )

            stop_reason |= _convergence_in_objective(objective)
            stop_reason |= _maximum_steps_exceeded(step)

            if stop_reason:
                return stop_reason

            if self._cancel_flag:
                raise self._Cancelled()

    def _optimise_step(self, λ: float, λ_cutoff: float, ssr: float) -> Tuple[float, float, float, '_StopReason']:
        J, residuals = self._calculate_jacobian()
        A = J.T @ J
        v = J.T @ residuals[:, 1]
        δ = -np.linalg.inv(A + λ * np.diag(np.diag(A))) @ v

        λ_next = λ
        λ_cutoff_next = λ_cutoff
        ssr_next = np.sum(residuals[:, 1]**2)

        stop_reason = 0

        if not math.isinf(ssr):
            R = (ssr - ssr_next) / (δ @ (-2*v - A@δ))

            if R < SLOW_CONVERGENCE_THRESHOLD:  # Slow convergence
                ν = 2 - (ssr_next - ssr) / (δ @ v)
                ν = np.clip(ν, 2, 10)

                if λ_next == 0:
                    λ_cutoff_next = 1 / (np.linalg.norm(np.linalg.inv(A), np.inf))
                    λ_next = λ_cutoff_next
                    ν /= 2

                λ_next *= ν
            elif R > FAST_CONVERGENCE_THRESHOLD:  # Fast convergence
                λ_next /= 2

                if 0 < λ_next < λ_cutoff:
                    λ_next = 0

        if ssr_next < ssr:
            self._profile_size = abs(residuals[:, 0]).max()
            self._residuals = residuals
            self._params += δ

            stop_reason |= _convergence_in_parameters(δ / self._params)
            stop_reason |= _convergence_in_gradient(v)
        else:
            # If error is worse, don't update parameters.
            ssr_next = ssr

        return λ_next, λ_cutoff_next, ssr_next, stop_reason

    def _calculate_jacobian(self) -> Tuple[np.ndarray, np.ndarray]:
        src_profile_xy = self._src_profile - (self.apex_x, self.apex_y)
        src_profile_rz = self._rz_from_xy(*src_profile_xy.T).T

        minimum_arclengths = np.empty((len(self._src_profile), 3))

        # [Initial guess for left side, Initial guess for right side]
        s_initial_guess = [-0.05 * max(self._profile_size, 4), 0.05 * max(self._profile_size, 4)]
        for i, (r, z) in enumerate(src_profile_rz):
            s, (e_r, e_z), steps_exceeded = \
                self._profile.closest(
                    p=(r, z),
                    s_0=s_initial_guess[r > 0],
                    max_steps=tolerances.MAXIMUM_ARCLENGTH_STEPS,
                    tol=tolerances.ARCLENGTH_TOL,
                )

            if steps_exceeded:
                self._logger(
                    'Warning: `minimum_arclength()` failed to converge in {} steps... (s_i = {:.4g})\n'
                    .format(tolerances.MAXIMUM_ARCLENGTH_STEPS, s)
                )

            minimum_arclengths[i] = s, e_r, e_z

            # Set initial guess of next point to result of current point
            s_initial_guess[r > 0] = s

        J = self._calculate_jacobian_row(*minimum_arclengths.T)
        residuals = np.stack(
            arrays=(
                minimum_arclengths[:, 0],
                np.copysign(np.linalg.norm(minimum_arclengths[:, (1, 2)], axis=1), minimum_arclengths[:, 1])
            ),
            axis=1)

        return J, residuals

    @overload
    def _calculate_jacobian_row(self, s: float, e_r: float, e_z: float) -> np.ndarray:
        """Calculate and return one row of the Jacobian"""

    @overload
    def _calculate_jacobian_row(self, s: Iterable[float], e_r: Iterable[float], e_z: Iterable[float]) -> np.ndarray:
        """Calculate and return many rows of the Jacobian"""

    def _calculate_jacobian_row(self, s, e_r, e_z):
        try:
            iter(s)
        except TypeError:
            return self._calculate_jacobian_row([s], [e_r], [e_z])[0]

        s, e_r, e_z = np.array((s, e_r, e_z))
        e_i = np.copysign(np.linalg.norm((e_r, e_z), axis=0), e_r)  # actual residual

        r_s, z_s, φ_s, dr_dB_s, dz_dB_s, dφ_dB_s = self._profile(s).T

        r = r_s + e_r
        z = z_s + e_z

        ddei_dxP, ddei_dyP = -self._xy_from_rz(e_r, e_z) / e_i      # derivative w.r.t X_0 and Y_0 (apex coordinates)
        ddei_dRP = -(e_r*r_s + e_z*z_s) / (self.apex_radius * e_i)  # derivative w.r.t. RP (apex radius)
        ddei_dBP = -(e_r*dr_dB_s + e_z*dz_dB_s) / e_i               # derivative w.r.t. Bo  (Bond number)
        ddei_dwP = (e_r*-z + e_z*r) / e_i                           # derivative w.r.t ω (rotational angle)

        return np.stack((ddei_dxP, ddei_dyP, ddei_dRP, ddei_dBP, ddei_dwP), axis=1)

    def _rz_from_xy(self, x: Union[float, Iterable[float]], y: Union[float, Iterable[float]]) -> np.ndarray:
        return self._apex_rot_matrix @ [x, y]

    def _xy_from_rz(self, r: Union[float, Iterable[float]], z: Union[float, Iterable[float]]) -> np.ndarray:
        return self._apex_rot_matrix.T @ [r, z]

    @property
    def _params(self) -> _Params:
        return self._params_

    @_params.setter
    def _params(self, new_params: Iterable[float]) -> None:
        new_params = self._Params(*new_params)

        self._params_ = new_params

        self._update_apex_rot_matrix()

        # Generate a new profile when parameters change
        self._update_profile()

        self._update_volsur()

        self._on_update(self)

    def _update_apex_rot_matrix(self) -> None:
        ω = self.rotation

        m = np.array([[cos(ω), -sin(ω)],
                      [sin(ω),  cos(ω)]])

        self._apex_rot_matrix = m

    def _update_profile(self) -> None:
        self._profile = equation.YoungLaplaceSolution(self.bond_number, self.apex_radius)

    def _update_volsur(self) -> None:
        """Update volume and surface area
        """
        self._volume, self._surface_area = equation.calculate_volsur(self.bond_number, self._profile_size)

        self._volume *= self.apex_radius**3
        self._surface_area *= self.apex_radius**2

    @property
    def degrees_of_freedom(self) -> int:
        return len(self._src_profile) - len(self._Params._fields) + 1

    @property
    def apex_x(self) -> float:
        return self._params.apex_x

    @property
    def apex_y(self) -> float:
        return self._params.apex_y

    @property
    def apex_radius(self) -> float:
        return self._params.apex_radius

    @property
    def bond_number(self) -> float:
        return self._params.bond_number

    @property
    def rotation(self) -> float:
        return self._params.rotation

    @property
    def volume(self) -> float:
        return self._volume

    @property
    def surface_area(self) -> float:
        return self._surface_area

    @overload
    def __call__(self, s: float) -> Tuple[float, float]:
        ...
    @overload
    def __call__(self, s: Iterable[float]) -> np.ndarray:
        ...
    def __call__(self, s):
        try:
            iter(s)
        except TypeError:
            return self.__call__([s])[0]

        r, z, *_ = self._profile(s).T
        x, y = self._xy_from_rz(r, z)

        data = np.stack((x, y), axis=1)
        data += (self.apex_x, self.apex_y)

        return data

    @property
    def residuals(self) -> Optional[np.ndarray]:
        return self._residuals

    @property
    def is_done(self) -> bool:
        return self._is_done

    @property
    def is_cancelled(self) -> bool:
        return self._is_cancelled

    # Thread-safe method to cancel the fit. Does nothing if fit has already finished.
    def cancel(self) -> None:
        self._cancel_flag = True


class _StopReason(IntEnum):
    CONVERGENCE_IN_PARAMETERS = 1
    CONVERGENCE_IN_GRADIENT = 2
    CONVERGENCE_IN_OBJECTIVE = 4
    MAXIMUM_STEPS_EXCEEDED = 8

    @classmethod
    def str_from_num(cls, v: int) -> str:
        """Return a human-readable string representation of `v` (a flag field)."""
        present_flag_names = []

        for flag in cls:
            if v & flag == flag:
                present_flag_names.append(flag.name)

        return ' | '.join(present_flag_names)


# Check for convergence in parameters
def _convergence_in_parameters(scaled_delta: np.ndarray) -> int:
    if abs(scaled_delta).max() < tolerances.DELTA_TOL:
        return _StopReason.CONVERGENCE_IN_PARAMETERS

    return 0


# Check for convergence in gradient
def _convergence_in_gradient(v: np.ndarray) -> int:
    if abs(v).max() < tolerances.GRADIENT_TOL:
        return _StopReason.CONVERGENCE_IN_GRADIENT

    return 0


# Check for convergence in objective function
def _convergence_in_objective(objective: float) -> int:
    if objective < tolerances.OBJECTIVE_TOL:
        return _StopReason.CONVERGENCE_IN_OBJECTIVE

    return 0


# Check if maximum steps exceeded
def _maximum_steps_exceeded(steps: int) -> int:
    if steps >= tolerances.MAXIMUM_FITTING_STEPS:
        return _StopReason.MAXIMUM_STEPS_EXCEEDED

    return 0
