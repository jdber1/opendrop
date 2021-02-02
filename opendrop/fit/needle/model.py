from typing import Tuple, Sequence
import numpy as np

from .types import NeedleParam


class NeedleModel:
    def __init__(self, data: Tuple[np.ndarray, np.ndarray]) -> None:
        self.data = np.copy(data)
        self.data.flags.writeable = False

        self._params = np.empty(len(NeedleParam))
        self._residuals = np.empty(shape=(self.data.shape[1],))
        self._jac = np.empty(shape=(self.data.shape[1], len(self._params)))

    def set_params(self, params: Sequence[float]) -> None:
        if (self._params == params).all():
            return

        w      = params[NeedleParam.ROTATION]
        radius = params[NeedleParam.RADIUS]
        X0     = params[NeedleParam.CENTER_X]
        Y0     = params[NeedleParam.CENTER_Y]

        residuals = self._residuals
        de_dw  = self._jac[:, NeedleParam.ROTATION]
        de_dR  = self._jac[:, NeedleParam.RADIUS]
        de_dX0 = self._jac[:, NeedleParam.CENTER_X]
        de_dY0 = self._jac[:, NeedleParam.CENTER_Y]

        Q = np.array([[np.cos(w), -np.sin(w)],
                      [np.sin(w),  np.cos(w)]])

        data_x, data_y = self.data
        data_r, data_z = Q.T @ (data_x - X0, data_y - Y0)

        e = np.abs(data_r) - radius

        rmask = data_r >= 0
        lmask = ~rmask

        residuals[:] = e
        de_dw[rmask] =  data_z[rmask]
        de_dw[lmask] = -data_z[lmask]
        de_dR[:] = -1
        de_dX0[rmask], de_dY0[rmask] = -Q.T[0]
        de_dX0[lmask], de_dY0[lmask] =  Q.T[0]

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
