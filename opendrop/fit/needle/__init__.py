from typing import Sequence, Tuple, NamedTuple

import numpy as np
import scipy.optimize

from .types import NeedleParam
from .model import NeedleModel
from .guess import needle_guess


__all__ = ('needle_fit',)


DELTA_TOL     = 1.e-8
GRADIENT_TOL  = 1.e-8
OBJECTIVE_TOL = 1.e-8


class NeedleFitResult(NamedTuple):
    rotation: float
    rho: float
    radius: float

    objective: float
    residuals: np.ndarray

    lmask: np.ndarray


def needle_fit(data: Tuple[np.ndarray, np.ndarray], verbose: bool = False):
    model = NeedleModel(data)

    def fun(params: Sequence[float], model: NeedleModel) -> np.ndarray:
        model.set_params(params)
        return model.residuals.copy()

    def jac(params: Sequence[float], model: NeedleModel) -> np.ndarray:
        model.set_params(params)
        return model.jac.copy()

    optimize_result = scipy.optimize.least_squares(
        fun,
        needle_guess(data),
        jac,
        args=(model,),
        x_scale='jac',
        method='trf',
        loss='cauchy',
        ftol=OBJECTIVE_TOL,
        xtol=DELTA_TOL,
        gtol=GRADIENT_TOL,
        verbose=2 if verbose else 0,
    )

    # Update model parameters to final result.
    model.set_params(optimize_result.x)

    result = NeedleFitResult(
        rotation=model.params[NeedleParam.ROTATION],
        rho=model.params[NeedleParam.RHO],
        radius=model.params[NeedleParam.RADIUS],

        objective=(model.residuals**2).sum()/model.dof,
        residuals=model.residuals,

        lmask=model.lmask,
    )

    return result
