import math
from typing import Sequence, Tuple, NamedTuple, Optional

import numpy as np
import scipy.optimize

from .types import NeedleParam
from .model import NeedleModel
from .guess import needle_guess


__all__ = ('NeedleFitResult', 'needle_fit',)


DELTA_TOL     = None
GRADIENT_TOL  = 1.e-8
OBJECTIVE_TOL = 1.e-8


class NeedleFitResult(NamedTuple):
    rotation: float
    rho: float
    radius: float

    objective: float
    residuals: np.ndarray

    lmask: np.ndarray


def needle_fit(
        data: Tuple[np.ndarray, np.ndarray],
        verbose: bool = False
) -> Optional[NeedleFitResult]:
    if data.shape[1] == 0:
        return None
    
    model = NeedleModel(data)

    def fun(params: Sequence[float], model: NeedleModel) -> np.ndarray:
        model.set_params(params)
        residuals = model.residuals.copy()
        return residuals

    def jac(params: Sequence[float], model: NeedleModel) -> np.ndarray:
        model.set_params(params)
        jac = model.jac.copy()
        return jac

    try:
        optimize_result = scipy.optimize.least_squares(
            fun,
            needle_guess(data),
            jac,
            args=(model,),
            x_scale='jac',
            method='trf',
            loss='arctan',
            f_scale=2.0,
            ftol=OBJECTIVE_TOL,
            xtol=DELTA_TOL,
            gtol=GRADIENT_TOL,
            max_nfev=50,
            verbose=2 if verbose else 0,
        )
    except ValueError:
        return None

    # Update model parameters to final result.
    model.set_params(optimize_result.x)

    result = NeedleFitResult(
        rotation=model.params[NeedleParam.ROTATION],
        rho=model.params[NeedleParam.RHO],
        radius=math.fabs(model.params[NeedleParam.RADIUS]),

        objective=(model.residuals**2).sum()/model.dof,
        residuals=model.residuals,

        lmask=model.lmask,
    )

    return result
