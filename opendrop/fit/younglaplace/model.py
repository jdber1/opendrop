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
from typing import Optional, Tuple, Iterable, overload, Any, Callable

import numpy as np
import scipy.optimize

from .shape import YoungLaplaceShape


MAXIMUM_FITTING_STEPS = 10

SLOW_CONVERGENCE_THRESHOLD = 0.25
FAST_CONVERGENCE_THRESHOLD = 0.75

DELTA_TOL               = 1.e-6
GRADIENT_TOL            = 1.e-6
OBJECTIVE_TOL           = 1.e-4


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


# noinspection NonAsciiCharacters
class YoungLaplaceFit:
    _Params = namedtuple('Params', ('bond', 'radius', 'x', 'y', 'rotation'))

    class _Cancelled(Exception):
        pass

    def __init__(
            self,
            data: np.ndarray,
            *,
            on_update: Optional[Callable[['YoungLaplaceFit'], Any]] = None,
            logger: Optional[Callable[[str], Any]] = None
    ) -> None:

        self._data = data
        self._params = self._Params(math.nan, math.nan, math.nan, math.nan, math.nan)

        self._cancel_flag = False
        self._is_cancelled = False
        self._is_done = False

        # The theoretical profile of the drop based on the current estimated parameters.
        self._shape = None  # type: Optional[YoungLaplaceShape]
        self._shape_size = 0.0
        self._residuals = np.empty((len(data), 2))

        self._on_update = on_update or (lambda _: None)
        self._logger = logger or (lambda _: None)

        self._fit()

    def _fit(self) -> None:
        # Guess the initial parameters
        self._update_params(young_laplace_guess(self._data))

        # Optimise
        try:
            stop_reason = self._optimise()
        except self._Cancelled:
            self._is_cancelled = True
            self._logger('\nCancelled.\n')
        except Exception as exc:
            # Unexpected error occurred in the fitting routine.
            buf = io.StringIO()
            traceback.print_exception(type(exc), exc, tb=exc.__traceback__, file=buf)
            self._logger('\n{}'.format(buf.getvalue()))
        else:
            self._logger('\nFitting finished ({})\n'.format(_StopReason.str_from_num(stop_reason)))

        self._is_done = True

        self._on_update(self)

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
                    apex_x=self._params.x,
                    apex_y=self._params.y,
                    apex_radius=self._params.radius,
                    bond_number=self._params.bond,
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
        stop_reason = 0

        J, residuals = self._calculate_jacobian()

        A = J.T @ J
        v = J.T @ residuals[:, 1]
        δ = -np.linalg.inv(A + λ * np.diag(np.diag(A))) @ v

        λ_next = λ
        λ_cutoff_next = λ_cutoff
        ssr_next = np.sum(residuals[:, 1]**2)

        if ssr_next < ssr:
            self._shape_size = abs(residuals[:, 0]).max()
            self._residuals = residuals
            self._update_params(self._params + δ)

            stop_reason |= _convergence_in_parameters(δ / self._params)
            stop_reason |= _convergence_in_gradient(v)
        else:
            # If error is worse, don't update parameters.
            ssr_next = ssr

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

        return λ_next, λ_cutoff_next, ssr_next, stop_reason

    def _calculate_jacobian(self) -> Tuple[np.ndarray, np.ndarray]:
        O, w = ((self.apex_x,), (self.apex_y,)), self.rotation
        W = np.array([[np.cos(w), -np.sin(w)],
                      [np.sin(w),  np.cos(w)]])

        data_rz = W @ (self._data.T - O)

        s = self._shape.closest(data_rz/self.apex_radius)
        r, z = rz = self.apex_radius * self._shape(s)
        dr_dBo, dz_dBo = self.apex_radius * self._shape.DBo(s)
        e_r, e_z = e_rz = data_rz - rz
        e = np.linalg.norm(e_rz, axis=0)

        de_dBo = -(e_r*dr_dBo + e_z*dz_dBo) / e             # derivative w.r.t. Bo (Bond number)
        de_dR = -(e_r*r + e_z*z) / (self.apex_radius * e)   # derivative w.r.t. R (apex radius)
        de_dX, de_dY = -(W.T @ e_rz) / e                    # derivative w.r.t. X and Y (apex coordinates)
        de_dw = (e_r*-z + e_z*r) / e                        # derivative w.r.t. ω (rotational angle)

        J = np.stack((de_dBo, de_dR, de_dX, de_dY, de_dw), axis=1)
        residuals = np.stack((s, e), axis=1)

        return J, residuals

    def _update_params(self, params: Iterable[float]) -> None:
        params = self._Params(*params)

        self._params = params

        # Generate new drop shape when parameters change.
        self._shape = YoungLaplaceShape(params.bond)

        # Invoke update callback.
        self._on_update(self)

    @property
    def degrees_of_freedom(self) -> int:
        return len(self._data) - len(self._Params._fields) + 1

    @property
    def apex_x(self) -> float:
        return self._params.x

    @property
    def apex_y(self) -> float:
        return self._params.y

    @property
    def apex_radius(self) -> float:
        return self._params.radius

    @property
    def bond_number(self) -> float:
        return self._params.bond

    @property
    def rotation(self) -> float:
        return self._params.rotation

    @property
    def volume(self) -> float:
        if self._shape is None:
            return math.nan

        return self._shape.volume(self._shape_size) * self.apex_radius**3

    @property
    def surface_area(self) -> float:
        if self._shape is None:
            return math.nan

        return self._shape.surface_area(self._shape_size) * self.apex_radius**2

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

        O, w = ((self.apex_x,), (self.apex_y,)), self.rotation
        W = np.array([[ np.cos(w),  np.sin(w)],
                      [-np.sin(w),  np.cos(w)]])

        rz = self._shape(s)
        xy = O + W @ rz

        return xy

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


def young_laplace_guess(data) -> None:
    center = np.mean(data, axis=0)
    radius = np.linalg.norm(data - center, axis=1).mean()

    result = scipy.optimize.least_squares(
        _circle_residues,
        (*center, radius),
        _circle_jac,
        args=(data,),
        loss='cauchy',  # Ignore outliers.
        x_scale=(radius, radius, radius),
    )

    center, radius = result.x[[0, 1]], result.x[2]
    residues = np.abs(result.fun)

    median = np.quantile(residues, 0.5)
    mask = residues < 10*median
    
    # Somewhat circular subarc of overall drop profile.
    spherish = data[mask].astype(float)

    angles = np.arctan2(spherish[:, 0] - center[0], -(spherish[:, 1] - center[1]))
    angles = np.unwrap(angles)

    # Estimate apex to be in the middle of the circular-ish subarc.
    rotation = (angles[0] + angles[-1])/2
    rotation_matrix = np.array([
        [np.cos(rotation), -np.sin(rotation)],
        [np.sin(rotation),  np.cos(rotation)],
    ])

    # Make a better estimate of the osculating circle at apex by fitting to a smaller subarc.
    cap = spherish[np.abs(angles - rotation) < 0.3]

    # Only try to improve the estimate if the small arc has more than 10 points.
    if len(cap) >= 10:
        result = scipy.optimize.least_squares(
            _circle_residues,
            (*center, radius),
            _circle_jac,
            args=(cap,),
            x_scale=(radius, radius, radius),
        )
        center, radius = result.x[[0, 1]], result.x[2]

    apex = center + radius * rotation_matrix @ [0, -1]

    # Estimate Bond number.
    normal = (rotation_matrix.T @ (data - apex).T) / radius
    z_sorted = normal[:, normal[1].argsort()]

    if np.searchsorted(z_sorted[1], 2.0) < z_sorted.shape[-1]:
        lower = np.searchsorted(z_sorted[1], 1.95, side='right')
        upper = np.searchsorted(z_sorted[1], 2.05, side='right')
        radii = np.abs(z_sorted[0][lower:upper])
        r = radii.mean()
        # From experimental data.
        bond = 0.1756 * r**2 + 0.5234 * r**3 - 0.2563 * r**4
    else:
        bond = 0.15

    # Restrict rotation to [-np.pi, np.pi]
    rotation = (rotation + np.pi) % (2*np.pi) - np.pi

    return (bond, radius, apex[0], apex[1], rotation)


def _circle_residues(params, data):
    center, radius = (params[0], params[1]), params[2]
    offset = data - center
    distances = np.linalg.norm(offset, axis=1)

    return distances - radius


def _circle_jac(params, data):
    center, radius = (params[0], params[1]), params[2]
    offset = data - center
    distances = np.linalg.norm(offset, axis=1)

    out = np.empty((len(data), 3))
    out[:, :2] = -offset/distances.reshape(-1, 1)
    out[:, 2] = -1

    return out


def _convergence_in_parameters(scaled_delta: np.ndarray) -> int:
    """Check for convergence in parameters."""
    if abs(scaled_delta).max() < DELTA_TOL:
        return _StopReason.CONVERGENCE_IN_PARAMETERS

    return 0


def _convergence_in_gradient(v: np.ndarray) -> int:
    """Check for convergence in gradient."""
    if abs(v).max() < GRADIENT_TOL:
        return _StopReason.CONVERGENCE_IN_GRADIENT

    return 0


def _convergence_in_objective(objective: float) -> int:
    """Check for convergence in objective function."""
    if objective < OBJECTIVE_TOL:
        return _StopReason.CONVERGENCE_IN_OBJECTIVE

    return 0


def _maximum_steps_exceeded(steps: int) -> int:
    """Check if maximum steps exceeded."""
    if steps >= MAXIMUM_FITTING_STEPS:
        return _StopReason.MAXIMUM_STEPS_EXCEEDED

    return 0
