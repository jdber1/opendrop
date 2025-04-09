from typing import Sequence
import numpy as np

from .types import CircleParam


class CircleModel:
    def __init__(self, data: np.ndarray) -> None:
        if data.flags.writeable:
            data = data.copy()
            data.flags.writeable = False

        self.data = data

        self._params = np.empty(len(CircleParam))
        self._params_set = False
        self._residuals = np.empty(shape=(self.data.shape[1],))
        self._jac = np.empty(shape=(self.data.shape[1], len(self._params)))
        self._lmask = np.empty(shape=(self.data.shape[1],), dtype=bool)

    def set_params(self, params: Sequence[float]) -> None:
        if self._params_set and (self._params == params).all():
            return

        xc = params[CircleParam.CENTER_X]
        yc = params[CircleParam.CENTER_Y]
        R  = params[CircleParam.RADIUS]

        e      = self._residuals
        de_dxc = self._jac[:, CircleParam.CENTER_X]
        de_dyc = self._jac[:, CircleParam.CENTER_Y]
        de_dR  = self._jac[:, CircleParam.RADIUS]

        x, y = self.data
        tx = x - xc
        ty = y - yc
        r = np.sqrt(tx**2 + ty**2)

        e[:] = r - R
        de_dxc[:] = -tx/r
        de_dyc[:] = -ty/r
        de_dR[:] = -1

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
