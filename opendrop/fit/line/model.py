from typing import Sequence
import numpy as np

from opendrop.utility.misc import rotation_mat2d

from .types import LineParam


class LineModel:
    def __init__(self, data: np.ndarray) -> None:
        if data.flags.writeable:
            data = data.copy()
            data.flags.writeable = False

        self.data = data

        self._params = np.empty(len(LineParam))
        self._params_set = False
        self._residuals = np.empty(shape=(self.data.shape[1],))
        self._jac = np.empty(shape=(self.data.shape[1], len(self._params)))
        self._lmask = np.empty(shape=(self.data.shape[1],), dtype=bool)

    def set_params(self, params: Sequence[float]) -> None:
        if self._params_set and (self._params == params).all():
            return

        q   = params[LineParam.ANGLE]
        rho = params[LineParam.RHO]

        e       = self._residuals
        de_dq   = self._jac[:, LineParam.ANGLE]
        de_drho = self._jac[:, LineParam.RHO]

        Q = rotation_mat2d(q)
        r, z = Q.T @ self.data - [[0], [rho]]

        e[:] = z
        de_dq[:] = -r
        de_drho[:] = -1

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
