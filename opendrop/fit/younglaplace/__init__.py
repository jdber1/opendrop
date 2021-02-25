from typing import Sequence, Tuple, NamedTuple

import numpy as np
import scipy.optimize

from .types import YoungLaplaceParam
from .model import YoungLaplaceModel
from .guess import young_laplace_guess


__all__ = ('YoungLaplaceFitResult', 'young_laplace_fit',)


DELTA_TOL     = 1.e-8
GRADIENT_TOL  = 1.e-8
OBJECTIVE_TOL = 1.e-8
MAX_STEPS     = 50


class YoungLaplaceFitResult(NamedTuple):
    bond: float
    radius: float
    apex_x: float
    apex_y: float
    rotation: float

    objective: float
    residuals: np.ndarray
    closest: np.ndarray
    arclengths: np.ndarray

    volume: float
    surface_area: float


def young_laplace_fit(data: Tuple[np.ndarray, np.ndarray], verbose: bool = False):
    model = YoungLaplaceModel(data)

    def fun(params: Sequence[float], model: YoungLaplaceModel) -> np.ndarray:
        model.set_params(params)
        return model.residuals

    def jac(params: Sequence[float], model: YoungLaplaceModel) -> np.ndarray:
        model.set_params(params)
        return model.jac

    optimize_result = scipy.optimize.least_squares(
        fun,
        young_laplace_guess(data),
        jac,
        args=(model,),
        x_scale='jac',
        method='lm',
        ftol=OBJECTIVE_TOL,
        xtol=DELTA_TOL,
        gtol=GRADIENT_TOL,
        verbose=2 if verbose else 0,
        max_nfev=MAX_STEPS,
    )

    # Update model parameters to final result.
    model.set_params(optimize_result.x)

    result = YoungLaplaceFitResult(
        bond=model.params[YoungLaplaceParam.BOND],
        radius=model.params[YoungLaplaceParam.RADIUS],
        apex_x=model.params[YoungLaplaceParam.APEX_X],
        apex_y=model.params[YoungLaplaceParam.APEX_Y],
        rotation=model.params[YoungLaplaceParam.ROTATION],

        objective=(model.residuals**2).sum()/model.dof,
        residuals=model.residuals,
        closest=model.closest,
        arclengths=model.arclengths,

        volume=model.volume,
        surface_area=model.surface_area,
    )

    return result
