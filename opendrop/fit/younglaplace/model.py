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


import math
from typing import Optional, Sequence, Tuple

import numpy as np

from opendrop.utility.misc import rotation_mat2d

from .shape import YoungLaplaceShape
from .types import YoungLaplaceParam


# Math constants.
PI = math.pi
NAN = math.nan


class YoungLaplaceModel:
    _shape: Optional[YoungLaplaceShape] = None

    def __init__(self, data: Tuple[np.ndarray, np.ndarray]) -> None:
        self.data = np.copy(data)
        self.data.flags.writeable = False

        self._params = np.empty(len(YoungLaplaceParam))
        self._params_set = False
        self._s = np.empty(shape=(self.data.shape[1],))
        self._residuals = np.empty(shape=(self.data.shape[1],))
        self._jac = np.empty(shape=(self.data.shape[1], len(self._params)))

    def set_params(self, params: Sequence[float]) -> None:
        if self._params_set and (self._params == params).all():
            return

        bond   = params[YoungLaplaceParam.BOND]
        radius = params[YoungLaplaceParam.RADIUS]
        X0     = params[YoungLaplaceParam.APEX_X]
        Y0     = params[YoungLaplaceParam.APEX_Y]
        w      = params[YoungLaplaceParam.ROTATION]

        s = self._s

        residuals = self._residuals
        de_dBo = self._jac[:, YoungLaplaceParam.BOND]
        de_dR  = self._jac[:, YoungLaplaceParam.RADIUS]
        de_dX0 = self._jac[:, YoungLaplaceParam.APEX_X]
        de_dY0 = self._jac[:, YoungLaplaceParam.APEX_Y]
        de_dw  = self._jac[:, YoungLaplaceParam.ROTATION]

        shape = self._get_shape(bond)
        Q = rotation_mat2d(w)

        data_x, data_y = self.data
        data_r, data_z = Q.T @ (data_x - X0, data_y - Y0)

        s[:] = shape.closest(data_r/radius, data_z/radius)
        r, z = radius * shape(s)
        dr_dBo, dz_dBo = radius * shape.DBo(s)
        e_r = data_r - r
        e_z = data_z - z
        e = np.hypot(e_r, e_z)

        # Set residues for points inside the drop as negative and outside as positive.
        e[np.signbit(e_r) != np.signbit(r)] *= -1

        residuals[:] = e
        de_dBo[:] = -(e_r*dr_dBo + e_z*dz_dBo) / e   # derivative w.r.t. Bond number
        de_dR[:] = -(e_r*r + e_z*z) / (radius * e)   # derivative w.r.t. radius
        de_dX0[:], de_dY0[:] = -Q @ (e_r, e_z) / e   # derivative w.r.t. apex (x, y)-coordinates
        de_dw[:] = (e_r*z - e_z*r) / e               # derivative w.r.t. rotation

        self._params[:] = params

    def _get_shape(self, bond: float) -> YoungLaplaceShape:
        if self._shape is None or self._shape.bond != bond:
            self._shape = YoungLaplaceShape(bond)

        return self._shape

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
    def closest(self) -> np.ndarray:
        xy = np.empty_like(self.data, dtype=float)

        bond   = self._params[YoungLaplaceParam.BOND]
        radius = self._params[YoungLaplaceParam.RADIUS]
        X0     = self._params[YoungLaplaceParam.APEX_X]
        Y0     = self._params[YoungLaplaceParam.APEX_Y]
        w      = self._params[YoungLaplaceParam.ROTATION]

        shape = self._get_shape(bond)
        Q = rotation_mat2d(w)
        s = self._s

        rz = radius * shape(s)
        xy[:] = Q @ rz + [[X0], [Y0]]

        return xy

    @property
    def arclengths(self) -> np.ndarray:
        s = self._s[:]
        s.flags.writeable = False
        return s

    @property
    def volume(self) -> float:
        bond   = self._params[YoungLaplaceParam.BOND]
        radius = self._params[YoungLaplaceParam.RADIUS]

        shape = self._get_shape(bond)
        s = self._s

        return radius**3 * shape.volume(s.max())

    @property
    def surface_area(self) -> float:
        bond   = self._params[YoungLaplaceParam.BOND]
        radius = self._params[YoungLaplaceParam.RADIUS]

        shape = self._get_shape(bond)
        s = self._s

        return radius**2 * shape.surface_area(s.max())
