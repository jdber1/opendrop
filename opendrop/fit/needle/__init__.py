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
    radius: float
    center_x: float
    center_y: float

    objective: float
    residuals: np.ndarray


def needle_fit(data: Tuple[np.ndarray, np.ndarray], verbose: bool = False):
    model = NeedleModel(data)

    def fun(params: Sequence[float], model: NeedleModel) -> np.ndarray:
        model.set_params(params)
        return model.residuals

    def jac(params: Sequence[float], model: NeedleModel) -> np.ndarray:
        model.set_params(params)
        jac = model.jac.copy()
        # Ignore CENTER_Y parameter because along with CENTER_X, Jacobian is degenerate.
        jac[:, NeedleParam.CENTER_Y] = 0
        return jac

    optimize_result = scipy.optimize.least_squares(
        fun,
        needle_guess(data),
        jac,
        args=(model,),
        x_scale='jac',
        method='lm',
        ftol=OBJECTIVE_TOL,
        xtol=DELTA_TOL,
        gtol=GRADIENT_TOL,
        verbose=2 if verbose else 0,
    )

    # Update model parameters to final result.
    model.set_params(optimize_result.x)

    result = NeedleFitResult(
        rotation=model.params[NeedleParam.ROTATION],
        radius=model.params[NeedleParam.RADIUS],
        center_x=model.params[NeedleParam.CENTER_X],
        center_y=model.params[NeedleParam.CENTER_Y],

        objective=(model.residuals**2).sum()/model.dof,
        residuals=model.residuals,
    )

    return result
