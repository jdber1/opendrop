from typing import Tuple, Sequence
import numpy as np

from .types import NeedleParam


class NeedleModel:
    def __init__(self, data: Tuple[np.ndarray, np.ndarray]) -> None:
        self.data = np.copy(data)
        self.data.flags.writeable = False

        self._params = np.empty(len(NeedleParam))
        self._params_set = False
        self._residuals = np.empty(shape=(self.data.shape[1],))
        self._jac = np.empty(shape=(self.data.shape[1], len(self._params)))
        self._lmask = np.empty(shape=(self.data.shape[1],), dtype=bool)

    def set_params(self, params: Sequence[float]) -> None:
        if self._params_set and (self._params == params).all():
            return

        w      = params[NeedleParam.ROTATION]
        rho    = params[NeedleParam.RHO]
        radius = params[NeedleParam.RADIUS]

        residuals = self._residuals
        de_dw   = self._jac[:, NeedleParam.ROTATION]
        de_drho = self._jac[:, NeedleParam.RHO]
        de_dR   = self._jac[:, NeedleParam.RADIUS]
        lmask   = self._lmask

        Q = np.array([[np.cos(w), -np.sin(w)],
                      [np.sin(w),  np.cos(w)]])

        data_x, data_y = self.data
        data_r, data_z = Q.T @ (data_x, data_y) - [[rho], [0]]

        e = np.abs(data_r) - radius

        lmask[:] = data_r < 0
        rmask    = ~lmask

        residuals[:] = e
        de_dw[rmask] =  data_z[rmask]
        de_dw[lmask] = -data_z[lmask]
        de_dR[:] = -1
        de_drho[rmask] = -1
        de_drho[lmask] =  1

        self._params[:] = params

    @property
    def params(self) -> Sequence[int]:
        params = self._params[:]
        params.flags.writeable = False
        return params

    @property
    def dof(self) -> int:
        return self.data.shape[1] - len(self.params) + 1

    @property
    def jac(self) -> np.ndarray:
        jac = self._jac[:]
        jac.flags.writeable = False
        return jac

    @property
    def residuals(self) -> np.ndarray:
        residuals = self._residuals[:]
        residuals.flags.writeable = False
        return residuals

    @property
    def lmask(self) -> np.ndarray:
        lmask = self._lmask[:]
        lmask.flags.writeable = False
        return lmask
