import asyncio
from concurrent.futures import ProcessPoolExecutor
from typing import Sequence, Tuple

import numpy as np

from opendrop.processing.ift import young_laplace
from opendrop.utility.geometry import Vector2


class YoungLaplaceFit:
    def __init__(
            self,
            bond: float,
            radius: float,
            arc_length: float,
            apex: Tuple[float, float],
            rotation: float,
            fitted_profile: np.ndarray,
            residuals: np.ndarray,
    ) -> None:
        self.bond = bond
        self.radius = radius
        self.arc_length = arc_length
        self.apex = Vector2(apex)
        self.rotation = rotation
        self.fitted_profile = fitted_profile
        self.residuals = residuals


def young_laplace_fit(profile: Sequence[Tuple[float, float]]) -> YoungLaplaceFit:
    fit = young_laplace.YoungLaplaceFit(profile)

    rotation = fit.rotation
    if rotation < -np.pi/2:
        rotation += np.pi
    elif rotation > np.pi/2:
        rotation -= np.pi

    residuals = fit.residuals
    residuals = residuals[residuals[:,0].argsort()]

    return YoungLaplaceFit(
        bond=fit.bond_number,
        radius=fit.apex_radius,
        arc_length=fit._profile_size,
        apex=(fit.apex_x, fit.apex_y),
        rotation=rotation,
        fitted_profile=fit(residuals[:,0]),
        residuals=residuals,
    )


class YoungLaplaceFitService:
    def __init__(self) -> None:
        self._executor = ProcessPoolExecutor()

    def fit(self, profile: Sequence[Tuple[float, float]]) -> asyncio.Future:
        cfut = self._executor.submit(young_laplace_fit, profile)
        fut = asyncio.wrap_future(cfut, loop=asyncio.get_event_loop())
        return fut

    def destroy(self) -> None:
        self._executor.shutdown()
