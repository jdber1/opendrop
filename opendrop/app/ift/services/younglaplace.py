import asyncio
from concurrent.futures import ProcessPoolExecutor
from typing import Tuple

import numpy as np

from opendrop.fit import YoungLaplaceFitResult, young_laplace_fit


__all__ = ('YoungLaplaceFitResult', 'YoungLaplaceFitService')


class YoungLaplaceFitService:
    def __init__(self) -> None:
        self._executor = ProcessPoolExecutor(max_workers=1)

    def fit(self, data: Tuple[np.ndarray, np.ndarray]) -> asyncio.Future:
        cfut = self._executor.submit(young_laplace_fit, data)
        fut = asyncio.wrap_future(cfut, loop=asyncio.get_event_loop())
        return fut

    def destroy(self) -> None:
        self._executor.shutdown()
