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


# Math constants.
PI = math.pi
NAN = math.nan


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
        self._params = self._Params(NAN, NAN, NAN, NAN, NAN)

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
        params = _young_laplace_guess(*self._data.T)
        self._update_params(params)

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
        O = [[self.apex_x],
             [self.apex_y]]
        w = self.rotation
        W = np.array([[np.cos(w), -np.sin(w)],
                      [np.sin(w),  np.cos(w)]])

        data_rz = W @ (self._data.T - O)

        s = self._shape.closest(data_rz/self.apex_radius)

        r, z = rz = self.apex_radius * self._shape(s)
        dr_dBo, dz_dBo = self.apex_radius * self._shape.DBo(s)
        e_r, e_z = e_rz = data_rz - rz
        e = np.hypot(e_r, e_z)

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

        # Create a new drop shape when parameters change.
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
            return NAN

        return self._shape.volume(self._shape_size) * self.apex_radius**3

    @property
    def surface_area(self) -> float:
        if self._shape is None:
            return NAN

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

        O = [[self.apex_x],
             [self.apex_y]]
        w = self.rotation
        W = np.array([[np.cos(w), -np.sin(w)],
                      [np.sin(w),  np.cos(w)]])

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

    def cancel(self) -> None:
        """Thread-safe method to cancel the fit. Does nothing if fit has already finished."""
        self._cancel_flag = True


def _young_laplace_guess(x: np.ndarray, y: np.ndarray) -> tuple:
    r, z, radius, apex_x, apex_y, rotation = _guess_rz_from_xy(x, y)
    bond = _bond_selected_plane(r, z, radius)

    return (bond, radius, apex_x, apex_y, rotation)


def _guess_rz_from_xy(x: np.ndarray, y: np.ndarray) -> tuple:
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
    r = unit_r @ [x - apex_x, y - apex_y]
    z = unit_z @ [x - apex_x, y - apex_y]

    # Restrict rotation to [-pi, pi].
    rotation = (rotation + PI) % (2*PI) - PI

    return r, z, radius, apex_x, apex_y, rotation


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
