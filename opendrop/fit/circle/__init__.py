from typing import Sequence, NamedTuple, Optional

import numpy as np
import scipy.optimize

from opendrop.geometry import Vector2
from .types import CircleParam
from .model import CircleModel


__all__ = ('CircleFitResult', 'circle_fit',)


DELTA_TOL     = 1.e-8
GRADIENT_TOL  = 1.e-8
OBJECTIVE_TOL = 1.e-8


class CircleFitResult(NamedTuple):
    center: Vector2[float]
    radius: float

    objective: float
    residuals: np.ndarray


def circle_fit(
        data: np.ndarray,
        *,
        loss: str = 'linear',
        f_scale: float = 1.0,

        xc: Optional[float] = None,
        yc: Optional[float] = None,
        radius: Optional[float] = None,

        verbose: bool = False,
) -> Optional[CircleFitResult]:
    if data.shape[1] == 0:
        return None
    
    model = CircleModel(data)

    def fun(params: Sequence[float]) -> np.ndarray:
        model.set_params(params)
        residuals = model.residuals.copy()
        return residuals

    def jac(params: Sequence[float]) -> np.ndarray:
        model.set_params(params)
        jac = model.jac.copy()
        return jac

    initial_params = np.empty(len(CircleParam))

    if xc is None or yc is None:
        xc, yc = data.mean(axis=1)

    if radius is None:
        tx, ty = data[0] - xc, data[1] - yc
        radius = np.median(np.sqrt(tx**2 + ty**2))

    initial_params[CircleParam.CENTER_X] = xc
    initial_params[CircleParam.CENTER_Y] = yc
    initial_params[CircleParam.RADIUS] = radius
    model.set_params(initial_params)

    try:
        optimize_result = scipy.optimize.least_squares(
            fun,
            model.params,
            jac,
            method='lm' if loss == 'linear' else 'trf',
            loss=loss,
            f_scale=f_scale,
            x_scale='jac',
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

    result = CircleFitResult(
        center=Vector2(model.params[CircleParam.CENTER_X],
                       model.params[CircleParam.CENTER_Y]),
        radius=model.params[CircleParam.RADIUS],

        objective=(model.residuals**2).sum()/model.dof,
        residuals=model.residuals,
    )

    return result
