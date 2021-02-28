from typing import Sequence, NamedTuple, Optional

import numpy as np
import scipy.optimize

from opendrop.geometry import Line2

from .types import LineParam
from .model import LineModel


__all__ = ('LineFitResult', 'line_fit',)


DELTA_TOL     = 1.e-8
GRADIENT_TOL  = 1.e-8
OBJECTIVE_TOL = 1.e-8


class LineFitResult(NamedTuple):
    angle: float
    rho: float

    objective: float
    residuals: np.ndarray


def line_fit(
        data: np.ndarray,
        *,
        loss: str = 'linear',
        f_scale: float = 1.0,
        verbose: bool = False,
) -> Optional[LineFitResult]:
    if data.shape[1] < 2:
        # Need at least two points to fit.
        return None
    
    model = LineModel(data)

    def fun(params: Sequence[float]) -> np.ndarray:
        model.set_params(params)
        residuals = model.residuals.copy()
        return residuals

    def jac(params: Sequence[float]) -> np.ndarray:
        model.set_params(params)
        jac = model.jac.copy()
        return jac

    model.set_params(line_guess(data))

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

    result = LineFitResult(
        angle=model.params[LineParam.ANGLE],
        rho=model.params[LineParam.RHO],

        objective=(model.residuals**2).sum()/model.dof,
        residuals=model.residuals,
    )

    return result


def line_guess(data: np.ndarray) -> Sequence[float]:
    """A very crude guess that just fits a line between two arbitrary points."""
    params = np.empty(len(LineParam))

    pt0 = data[:,  0]
    pt1 = data[:, -1]

    if np.all(pt0 == pt1):
        # Just initialize to anything.
        params[LineParam.RHO] = 0
        params[LineParam.ANGLE] = 0
    else:
        line = Line2(data[:, 0], data[:, -1])
        unit = line.unit
        perp = line.perp

        params[LineParam.RHO] = line.perp @ line.pt0
        params[LineParam.ANGLE] = np.arctan2(unit.y, unit.x)

    return params
