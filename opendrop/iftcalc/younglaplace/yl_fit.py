import asyncio
import itertools
import math
import time
import traceback
from enum import IntEnum, Enum
from math import cos, sin
from os.path import devnull
from typing import Optional, Tuple, Union, Iterable, IO, Callable, overload

import numpy as np
from scipy import integrate, interpolate as sp_interpolate

from opendrop.utility.events import Event
from opendrop.utility.misc import clamp
from . import best_guess
from . import de
from . import tolerances

RESPONSIVENESS = 0.015  # type: float
last_paused = 0.0  # type: float


# test for convergence in parameters
def _convergence_in_parameters(scaled_delta):
    if abs(scaled_delta).max() < tolerances.DELTA_TOL:
        return YoungLaplaceFit.StopFlag.CONVERGENCE_IN_PARAMETERS

    return 0


# test for convergence in gradient
def _convergence_in_gradient(v):
    if abs(v).max() < tolerances.GRADIENT_TOL:
        return YoungLaplaceFit.StopFlag.CONVERGENCE_IN_GRADIENT

    return 0


# test for convergence in objective function
def _convergence_in_objective(objective):
    if objective < tolerances.OBJECTIVE_TOL:
        return YoungLaplaceFit.StopFlag.CONVERGENCE_IN_OBJECTIVE

    return 0


# test maximum steps
def _maximum_steps_exceeded(steps):
    if steps >= tolerances.MAXIMUM_FITTING_STEPS:
        return YoungLaplaceFit.StopFlag.MAXIMUM_STEPS_EXCEEDED

    return 0


# the function g(s) used in finding the arc length for the minimal distance
def f_Newton(e_r, e_z, φ, dφ_dt, apex_radius):
    f = - (e_r * cos(φ) + e_z * sin(φ)) / (apex_radius + dφ_dt * (e_r * sin(φ) - e_z * cos(φ)))
    return f


class FitCancelled(Exception):
    pass


# noinspection NonAsciiCharacters
class YoungLaplaceFit:
    PARAMETER_DIMENSIONS = 5

    class Status(Enum):
        INITIALISED = 0
        FITTING = 1
        FINISHED = 2

    class StopFlag(IntEnum):
        CONVERGENCE_IN_PARAMETERS = 1
        CONVERGENCE_IN_GRADIENT = 2
        CONVERGENCE_IN_OBJECTIVE = 4
        MAXIMUM_STEPS_EXCEEDED = 8
        CANCELLED = 16
        UNEXPECTED_EXCEPTION = 32

        @classmethod
        def str_from_num(cls, v: int) -> str:
            """Return a human-readable string representation of `v` (a flag field)."""
            present_flag_names = []

            for flag in cls:
                if v & flag == flag:
                    present_flag_names.append(flag.name)

            return ' | '.join(present_flag_names)

    # Contour must have coordinates with y-axis pointing upwards (opposite gravity).
    def __init__(self, contour: np.ndarray, log_file: IO = open(devnull, 'w')) -> None:
        self.on_params_changed = Event()

        self._contour = contour[contour[:, 1].argsort()]  # type: np.ndarray
        self._log_file = log_file

        self._status_ = YoungLaplaceFit.Status.INITIALISED  # type: YoungLaplaceFit.Status
        self._stop_flags = 0  # type: YoungLaplaceFit.StopFlag
        self._cancelled = False  # type: bool

        self._params_ = None
        self._apex_rot_matrix = np.identity(2)

        # The theoretical profile of the drop based on the current estimated parameters.
        self._profile = None  # type: Optional[sp_interpolate.CubicSpline]
        self._profile_samples_ = 5000  # type: int
        self._profile_interpolation_domain_ = 4.0  # type: float
        self._profile_domain = 0  # type: float

        # Levenberg–Marquardt–Fletcher (LMF)
        self._lmf_step_ = 0  # type: int

        self._objective_ = math.inf  # type: float
        self._residuals = None  # type: Optional[np.ndarray]

        # Guess the initial parameters.
        self._initial_guess()

    def _initial_guess(self) -> None:
        """Initialises parameters to a first best guess"""
        apex_x, apex_y, apex_radius = best_guess.fit_circle(self._contour)

        bond_number = best_guess.bond_number(self._contour, apex_x, apex_y, apex_radius)
        omega_rotation = 0.0
        self._params = [apex_x, apex_y, apex_radius, bond_number, omega_rotation]

    async def optimise(self) -> None:
        self._status = YoungLaplaceFit.Status.FITTING

        try:
            # Improve the initial guess and fit the parameters to the input contour data.
            await self._optimise()
            # Log that the fitting has finished.
            self._log('\nFitting finished ({})'.format(YoungLaplaceFit.StopFlag.str_from_num(self.stop_flags)))
        except FitCancelled:
            # Log that fitting has been cancelled.
            self._log('\nCancelled.')
            self._stop_flags = YoungLaplaceFit.StopFlag.CANCELLED
        except Exception as exc:  # Unexpected error occurred in the fitting routine.
            # Log that an unexpected error has occurred.
            self._log()  # log an empty line
            traceback.print_exception(type(exc), exc, tb=exc.__traceback__, file=self._log_file)
            self._stop_flags = YoungLaplaceFit.StopFlag.UNEXPECTED_EXCEPTION
        finally:
            # Mark that fitting has finished.
            self._status = YoungLaplaceFit.Status.FINISHED

    async def _optimise(self) -> None:
        assert self._params is not None

        degrees_of_freedom = len(self._contour) - self.PARAMETER_DIMENSIONS + 1  # type: int

        ρ = 0.25  # type: float
        σ = 0.75  # type: float

        λ = 0  # type: float

        self._log('{: >4}  {: >10}  {: >10}  {: >10}  {: >11}  {: >10}  {:>11}'.format(
            'Step', 'Objective', 'x-centre', 'z-centre', 'Apex radius', 'Bond', 'Image angle'
        ))

        # Initialise sum of squared residuals to be arbitrarily large.
        ssr = math.inf

        for self._lmf_step in itertools.count():
            J, residuals = await self._calculate_jacobian()

            A = J.T @ J
            v = J.T @ residuals[:, 1]

            ssr_next = np.sum(residuals[:, 1]**2)

            A_plus_λdiagA = A + λ * np.diag(np.diag(A))
            A_plus_λdiagA_inv = np.linalg.inv(A_plus_λdiagA)
            δ = -A_plus_λdiagA_inv @ v

            if self._lmf_step > 0:
                R = (ssr - ssr_next) / (δ @ (-2*v - A.T@δ))

                if R < ρ:  # Slow convergence
                    ν = clamp(2 - (ssr_next - ssr) / δ @ v, lower=2, upper=10)

                    if λ == 0:
                        λ_c = 1 / abs(A_plus_λdiagA_inv).max()
                        λ = λ_c

                        ν /= 2

                    λ *= ν
                elif R > σ:  # Rapid convergence
                    λ /= 2

                    if λ != 0 and λ < λ_c:  # todo: λ_c may not be defined yet?
                        λ = 0

            # If residuals reduces accept (will always accept first run since ssr initialised as inf)
            if ssr_next < ssr:
                self._profile_domain = abs(residuals[:, 0]).max()
                self._objective = ssr_next / degrees_of_freedom
                self._residuals = residuals
                self._improve_params(δ)

                ssr = ssr_next

                self._stop_flags |= _convergence_in_gradient(v)

            # Log the fitting progress
            self._log('{: >4d} {: >11.4g} {: >11.4g} {: >11.4g}  {: >11.4g} {: >11.4g} {: >11.4g}°'.format(
                self._lmf_step, self._objective, *self._params[:-1], math.degrees(self.apex_rot)
            ))

            # Check if any stopping criteria are met.
            if self._stop_flags:
                return

    async def _calculate_jacobian(self) -> Tuple[np.ndarray, np.ndarray]:
        contour_xy = self._contour - (self.apex_x, self.apex_y)
        contour_rz = self.rz_from_xy(*contour_xy.T).T

        minimum_arclengths = np.empty((len(self._contour), 3))

        # [closest s for left side, closest s for right side]
        t_last_closest = [0.05 * self._profile_interpolation_domain] * 2
        for i, (r, z) in enumerate(contour_rz):
            await self._housekeeping()
            t, e_r, e_z = self._minimum_arclength(r, z, t_0=abs(t_last_closest[r < 0]))
            if r < 0:
                t, e_r = -t, -e_r

            minimum_arclengths[i] = t, e_r, e_z
            t_last_closest[r < 0] = t

        J = self._calculate_jacobian_row(*minimum_arclengths.T)
        residuals = np.stack(
            (minimum_arclengths[:, 0],
             np.copysign(np.linalg.norm(minimum_arclengths[:, (1, 2)], axis=1), minimum_arclengths[:, 1])),
            axis=1)

        return J, residuals

    @overload
    def _calculate_jacobian_row(self, t: float, e_r: float, e_z: float) -> np.ndarray:
        """Calculate and return one row of the Jacobian"""

    @overload
    def _calculate_jacobian_row(self, t: Iterable[float], e_r: Iterable[float], e_z: Iterable[float]) -> np.ndarray:
        """Calculate and return many rows of the Jacobian"""

    def _calculate_jacobian_row(self, t, e_r, e_z):
        if isinstance(t, float) or isinstance(t, int):
            return self._calculate_jacobian_row([t], [e_r], [e_z])[0]

        t, e_r, e_z = np.array((t, e_r, e_z))
        e_i = np.copysign(np.linalg.norm((e_r, e_z), axis=0), e_r)  # actual residual

        u_t, v_t, φ_t, du_dB_t, dv_dB_t, dφ_dB_t = self._profile(abs(t)).T
        u_t[t < 0] *= -1
        du_dB_t[t < 0] *= -1

        apex_radius = self.apex_radius
        r_t = apex_radius * u_t
        z_t = apex_radius * v_t
        dr_dB_s = apex_radius * du_dB_t
        dz_dB_s = apex_radius * dv_dB_t

        r = r_t + e_r
        z = z_t + e_z

        ddei_dxP, ddei_dyP = -self.xy_from_rz(e_r, e_z) / e_i  # derivative w.r.t X_0 and Y_0 (apex coordinates)
        ddei_dRP = -(e_r*u_t + e_z*v_t) / e_i                  # derivative w.r.t. RP (apex radius)
        ddei_dBP = -(e_r*dr_dB_s + e_z*dz_dB_s) / e_i          # derivative w.r.t. Bo  (Bond number)
        ddei_dwP = (e_r*-z + e_z*r) / e_i                      # derivative w.r.t ω (rotational angle)

        return np.stack((ddei_dxP, ddei_dyP, ddei_dRP, ddei_dBP, ddei_dwP), axis=1)

    # Calculate the minimum theoretical point to the point (r,z)
    def _minimum_arclength(self, r: float, z: float, t_0: float) -> Tuple[float, float, float]:
        r = abs(r)

        apex_radius = self.apex_radius
        bond_number = self.bond_number

        flag_bump = 0
        t, e_r, e_z = t_0, 0, 0
        for _ in range(tolerances.MAXIMUM_ARCLENGTH_STEPS):
            u_t, v_t, φ_t, du_dB_t, dv_dB_t, dφ_dB_t = self._profile_safe_eval_at(t)

            e_r = r - apex_radius * u_t
            e_z = z - apex_radius * v_t

            dφ_ds = 2 - bond_number * v_t - sin(φ_t) / u_t

            t_next = t - f_Newton(e_r, e_z, φ_t, dφ_ds, apex_radius)

            if t_next < 0:  # arc length outside integrated region
                t_next = 0
                flag_bump += 1

            if flag_bump >= 2:  # has already been pushed back twice - abort
                break

            if abs(t_next - t) < tolerances.ARCLENGTH_TOL:
                break

            t = t_next
        else:
            self._log('Warning: `minimum_arclength()` failed to converge in {} steps... (s_i = {:.4g})'
                      .format(tolerances.MAXIMUM_ARCLENGTH_STEPS, t))

        return t, e_r, e_z

    async def _housekeeping(self, now: Callable[[], float] = time.time) -> None:
        global last_paused

        now = now()
        if now - last_paused > RESPONSIVENESS:
            last_paused = now

            # Hand back control to the event loop to allow the GUI to remain responsive.
            await asyncio.sleep(0)

        # If something set `self._cancelled` to True, then raise a FitCancelled exception.
        if self._cancelled:
            raise FitCancelled

    # interpolate the theoretical profile data, evaluating it at `s`, `s` can be one value or an array of values. The
    # interpolated region will be automatically expanded if `s` is too large.
    def _profile_safe_eval_at(self, s: Union[float, Iterable[float]]) -> np.ndarray:
        if self._profile is None:
            raise ValueError(
                "Not all parameters have been specified, profile has not yet been generated"
            )

        try:
            s_min = min(s)
            s_max = max(s)
        except TypeError:
            s_min = s
            s_max = s

        if s_min < 0:
            raise ValueError('s-value outside domain, got {}'.format(s_min))

        # If the profile is evaluated outside of the interpolated region, expand it by 20%.
        if s_max > self._profile_interpolation_domain:
            self._profile_interpolation_domain = 1.2 * s_max

        return self._profile(s)

    # generate a new drop profile
    def _update_profile(self) -> None:
        if all(v is not None for v in (self._profile_interpolation_domain, self._profile_samples, self._params)):
            s_data = np.linspace(0, self._profile_interpolation_domain, self._profile_samples)

            # EPS = .000001 # need to use Bessel function Taylor expansion below
            x_vec_initial = [.000001, 0., 0., 0., 0., 0.]

            sampled_data = integrate.odeint(de.ylderiv, x_vec_initial, s_data, args=(self.bond_number,))

            # Boundary conditions for the spline
            bc = ((1, de.ylderiv(sampled_data[0], 0, self.bond_number)),
                  (1, de.ylderiv(sampled_data[-1], 0, self.bond_number)))

            # todo: make sure theoretical data is all finite, otherwise log the error and halt fit

            self._profile = sp_interpolate.CubicSpline(
                x=s_data, y=sampled_data, bc_type=bc
            )
        else:
            self._profile = None

    def _improve_params(self, delta: Tuple) -> None:
        if len(delta) != self.PARAMETER_DIMENSIONS:
            raise ValueError(
                "Parameter array incorrect dimensions, expected {0}, got {1}"
                    .format(self.PARAMETER_DIMENSIONS, len(delta))
            )

        delta = np.array(delta)

        old_params = tuple(self._params_)
        assert old_params is not None

        self._params += delta
        self._stop_flags |= _convergence_in_parameters(delta / self._params)

    def _update_apex_rot_matrix(self) -> None:
        ω = self.apex_rot

        m = np.array([[cos(ω), -sin(ω)],
                      [sin(ω),  cos(ω)]])

        self._apex_rot_matrix = m

    def rz_from_xy(self, x: Union[float, Iterable[float]], y: Union[float, Iterable[float]]) -> np.ndarray:
        return self._apex_rot_matrix @ [x, y]

    def xy_from_rz(self, r: Union[float, Iterable[float]], z: Union[float, Iterable[float]]) -> np.ndarray:
        return self._apex_rot_matrix.T @ [r, z]

    def _log(self, *args, **kwargs) -> None:
        print(*args, **kwargs, file=self._log_file)

    def cancel(self) -> None:
        self._cancelled = True

    @property
    def _status(self) -> 'YoungLaplaceFit.Status':
        return self._status_

    @_status.setter
    def _status(self, new_status: 'YoungLaplaceFit.Status') -> None:
        self._status_ = new_status

    @property
    def _lmf_step(self) -> int:
        return self._lmf_step_

    @_lmf_step.setter
    def _lmf_step(self, value: int) -> None:
        self._lmf_step_ = value
        self._stop_flags |= _maximum_steps_exceeded(self._lmf_step_)

    @property
    def _params(self) -> Tuple:
        params = self._params_
        if self._params_ is None:
            params = itertools.repeat(math.nan, self.PARAMETER_DIMENSIONS)

        return tuple(params)

    @_params.setter
    def _params(self, new_params: Tuple) -> None:
        if len(new_params) != self.PARAMETER_DIMENSIONS:
            raise ValueError(
                "Parameter array incorrect dimensions, expected {0}, got {1}"
                    .format(self.PARAMETER_DIMENSIONS, len(new_params))
            )

        self._params_ = new_params

        self._update_apex_rot_matrix()  # update wP rotation matrix
        self._update_profile()  # generate new profile when the parameters are changed

        self.on_params_changed.fire()

    @property
    def _profile_interpolation_domain(self) -> float:
        return self._profile_interpolation_domain_

    @_profile_interpolation_domain.setter
    def _profile_interpolation_domain(self, value: float):
        if not value > 0:
            raise ValueError("Profile interpolation domain must be positive, got {}".format(value))

        self._profile_interpolation_domain_ = value

        # Update the profile, generating data points up to the new interpolation domain.
        self._update_profile()

    @property
    def _profile_samples(self) -> int:
        return self._profile_samples_

    @_profile_samples.setter
    def _profile_samples(self, value: int):
        if not value > 1:
            raise ValueError("Number of samples must be > 1, got {}".format(value))

        self._profile_samples_ = value

        self._update_profile()  # generate new profile when steps changed

    @property
    def _objective(self) -> float:
        return self._objective_

    @_objective.setter
    def _objective(self, value: float) -> None:
        self._objective_ = value
        self._stop_flags |= _convergence_in_objective(self._objective_)

    @property
    def status(self) -> 'YoungLaplaceFit.Status':
        return self._status

    @property
    def stop_flags(self) -> 'YoungLaplaceFit.StopFlag':
        return self._stop_flags

    @property
    def params(self) -> Tuple:
        return self._params

    @property
    def apex_x(self) -> float:
        return self._params[0]

    @property
    def apex_y(self) -> float:
        return self._params[1]

    @property
    def apex_radius(self) -> float:
        return self._params[2]

    @property
    def bond_number(self) -> float:
        return self._params[3]

    @property
    def apex_rot(self) -> float:
        return self._params[4]

    @property
    def profile(self) -> Optional[sp_interpolate.CubicSpline]:
        return self._profile

    @property
    def profile_domain(self) -> float:
        return self._profile_domain

    @property
    def objective(self) -> float:
        return self._objective

    @property
    def residuals(self) -> Optional[np.ndarray]:
        return self._residuals
