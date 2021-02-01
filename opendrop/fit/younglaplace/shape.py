from functools import lru_cache, partial
import typing
from typing import Sequence, Optional, Tuple

import numpy as np
import scipy.integrate, scipy.optimize


__all__ = ('YoungLaplaceShape',)

INIT_SOLVED_SIZE = 4.0
MAX_SOLVED_SIZE = 10.0

MAX_CLOSEST_ITERATIONS = 10
CLOSEST_TOL = 1.e-6

# Very tiny float for managing singularities.
INFITESIMAL = np.spacing(0.)
PI = np.pi


class YoungLaplaceShape:
    def __init__(self, bond: float) -> None:
        self.bond = bond

        self._s = [0.]
        self._y = [(
        #   r           z
            0.        , 0.,
        #   dr/ds       dz/ds
            1.        , 0.,
        #   dr/dBo      dz/dBo
            0.        , 0.,
        #   d2r/dBods  d2z/dBods
            0.        , 0.,
        )]
        self._interpolants = []
        self._z_inv_table = ([self._y[-1][1]], [self._s[-1]])
        self._z_max_solved = False

        self._solver = scipy.integrate.RK45(
            fun=partial(young_laplace_ode_combined, bond=bond),
            t0=self._s[-1],
            y0=self._y[-1],
            t_bound=MAX_SOLVED_SIZE,
            # Using vectorized=False is faster for some reason.
            vectorized=False,
        )

        self._step_until_s(INIT_SOLVED_SIZE)

    def __call__(self, s: np.ndarray) -> np.ndarray:
        r_and_z = self._eval(s)[[0,1]]
        return r_and_z

    def DBo(self, s: np.ndarray) -> np.ndarray:
        drz_dBo = self._eval(s)[[4,5]]
        return drz_dBo

    def _eval(self, s: np.ndarray) -> np.ndarray:
        result = np.empty(shape=(len(self._y[0]), len(s)))

        s_abs = np.abs(s)

        # Sort descending and then reverse so NaNs get accumulated at the start and the last element is always
        # the largest.
        order = np.argsort(-s_abs)[::-1]
        unorder = np.empty_like(order)
        unorder[order] = np.arange(len(order))

        s_abs_ordered = s_abs[order]

        self._step_until_s(s_abs[-1])

        partition = np.searchsorted(s_abs_ordered, self._s[1:-1], side='right')
        subintervals = np.split(s_abs_ordered, partition)
        subresults = np.split(result, partition, axis=1)

        for subresult, subinterval, func in zip(subresults, subintervals, self._interpolants):
            subresult[:] = func(subinterval)

        result = result[:, unorder]

        # Flip signs of r, dz/ds, dr/dBo, d2z/dBods where negative s queried.
        result[[0, 3, 4, 7], np.argwhere(s < 0)] *= -1

        return result

    def z_inv(self, z: Sequence[float]) -> np.ndarray:
        result = np.interp(z, *self._z_inv_table, left=np.nan, right=np.nan) 

        # Fast check for nan: https://stackoverflow.com/q/6736590.
        if np.isnan(np.sum(result, where=(z > 0))) and not self._z_max_solved:
            self._step_until_z(np.nanmax(z))
            result = np.interp(z, *self._z_inv_table, left=np.nan, right=np.nan) 

        return result

    def volume(self, s: float) -> float:
        return self._volsur(s)[0]

    def surface_area(self, s: float) -> float:
        return self._volsur(s)[1]

    @lru_cache
    def _volsur(self, s: float) -> Tuple[float, float]:
        y0 = [0., 0., 1., 0., 0., 0.]

        return scipy.integrate.odeint(
            volsur_ode,
            y0,
            t=[0, s],
            args=(self.bond,),
            tfirst=True,
        )[-1][-2:]

    def _step_until_s(self, s: float) -> None:
        if self._s[-1] >= s:
            return

        while self._s[-1] < s:
            if not self._step():
                break

    def _step_until_z(self, z: float) -> None:
        if self._z_inv_table[0][-1] >= z:
            return

        while self._z_inv_table[0][-1] < z or not self._z_max_solved:
            if not self._step():
                break

    def _step(self) -> bool:
        if self._solver.status in ('finished', 'failed'):
            return False

        self._solver.step()
        if self._solver.status == 'failed':
            return False

        s = self._solver.t
        y = self._solver.y
        interpolant = self._solver.dense_output()

        self._s.append(s)
        self._y.append(y)
        self._interpolants.append(interpolant)

        if not self._z_max_solved:
            z = y[1]
            s_at_z = s

            z_max_event = self._check_z_max_event()
            if z_max_event is not None:
                z = self._eval(np.array(z_max_event).reshape(1))[1][0]
                s_at_z = z_max_event
                self._z_max_solved = True

            self._z_inv_table[0].append(z)
            self._z_inv_table[1].append(s_at_z)

        return True

    def _check_z_max_event(self) -> Optional[float]:
        interpolant = self._interpolants[-1]
        s_old = interpolant.t_min
        s = interpolant.t_max
        z_old = interpolant(s_old)[1]
        z, dz_ds = interpolant(s)[[1, 3]]

        if z > z_old and dz_ds > 0:
            # Looks like z is still monotonically increasing.
            return

        event = scipy.optimize.fminbound(
            func=lambda s: -interpolant(s)[1],
            x1=s_old,
            x2=s,
            full_output=False,
        )

        return typing.cast(float, event)

    def closest(self, data_r: np.ndarray, data_z: np.ndarray):
        s = np.empty(len(data_r))

        pos_z = data_z > 0
        neg_r = data_r < 0

        s[~pos_z] = 0
        s[pos_z] = self.z_inv(data_z[pos_z])
        s[neg_r] *= -1

        np.nan_to_num(s, nan=self._z_inv_table[1][-1], copy=False)

        for _ in range(MAX_CLOSEST_ITERATIONS):
            s_prev, s = s, self._closest_next(data_r, data_z, s)
            if np.abs(s - s_prev).max() < CLOSEST_TOL:
                break

        return s

    def _closest_next(self, data_r: np.ndarray, data_z: np.ndarray, s: np.ndarray):
        predict = self._eval(s)
        r, z = predict[[0, 1]]
        dr_ds, dz_ds = predict[[2,3]]
        d2r_ds2, d2z_ds2 = self._d2_ds2(s, r, z, dr_ds, dz_ds)

        e_r = data_r - r
        e_z = data_z - z

        f = -2 * (e_r*dr_ds + e_z*dz_ds)
        fprime = -2 * (-1 + e_r*d2r_ds2 + e_z*d2z_ds2)

        # Newton optimization except avoid maximas.
        s_next = s - f/np.abs(fprime)

        return s_next

    def _d2_ds2(
            self,
            s: Sequence[float],
            r: Sequence[float],
            z: Sequence[float],
            dr_ds: Sequence[float],
            dz_ds: Sequence[float],
    ) -> np.ndarray:
        return young_laplace_ode(s, r, z, dr_ds, dz_ds, self.bond)


def young_laplace_ode_combined(s, y, bond):
    """Young--Laplace system of differential equations.
    """
    r, z, dr_ds, dz_ds, dr_dBo, dz_dBo, d2r_dBods, d2z_dBods = y

    d2r_ds2, d2z_ds2 = young_laplace_ode(
        s, r, z, dr_ds, dz_ds,
        bond,
    )

    d3r_dBods2, d3z_dBods2 = young_laplace_ode_DBo(
        s, r, z, dr_ds, dz_ds, dr_dBo, dz_dBo, d2r_dBods, d2z_dBods,
        bond,
    )

    return np.array([dr_ds, dz_ds, d2r_ds2, d2z_ds2, d2r_dBods, d2z_dBods, d3r_dBods2, d3z_dBods2])


def young_laplace_ode(s, r, z, dr_ds, dz_ds, bond):
    dphi_ds = 2 - bond*z - (dz_ds + INFITESIMAL)/(r + INFITESIMAL)

    d2r_ds2 = -dz_ds * dphi_ds
    d2z_ds2 = dr_ds * dphi_ds

    return d2r_ds2, d2z_ds2


def young_laplace_ode_DBo(s, r, z, dr_ds, dz_ds, dr_dBo, dz_dBo, d2r_dBods, d2z_dBods, bond):
    dphi_ds = 2 - bond*z - (dz_ds + INFITESIMAL)/(r + INFITESIMAL)
    d2phi_dBods = -z - dz_dBo*bond - d2z_dBods/(r + INFITESIMAL) + dr_dBo*dz_ds/(r**2 + INFITESIMAL)
    d3r_dBods2 = -d2z_dBods*dphi_ds - d2phi_dBods*dz_ds
    d3z_dBods2 = d2r_dBods*dphi_ds + d2phi_dBods*dr_ds

    return d3r_dBods2, d3z_dBods2


def volsur_ode(s, y, bond):
    r, z, dr_ds, dz_ds, vol, sur = y

    dphi_ds = 2 - bond*z - (dz_ds + INFITESIMAL)/(r + INFITESIMAL)

    d2r_ds2 = -dz_ds * dphi_ds
    d2z_ds2 = dr_ds * dphi_ds
    dvol_ds = PI * r**2 * dz_ds
    dsur_ds = 2 * PI * r

    return [dr_ds, dz_ds, d2r_ds2, d2z_ds2, dvol_ds, dsur_ds]
