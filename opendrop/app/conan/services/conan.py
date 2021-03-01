from abc import abstractmethod
import asyncio
from concurrent.futures import ProcessPoolExecutor
from typing import Optional, Protocol

import numpy as np
from injector import inject

from opendrop.geometry import Line2
from opendrop.fit import contact_angle_fit, ContactAngleFitResult as ConanFitResult

from .params import ConanParamsFactory


__all__ = ('ConanFitResult', 'ConanFitService')


class ConanFitParams(Protocol):
    @property
    @abstractmethod
    def baseline(self) -> Optional[Line2]: ...


class ConanFitService:
    @inject
    def __init__(self, default_params_factory: ConanParamsFactory) -> None:
        self._executor = ProcessPoolExecutor(max_workers=1)
        self._default_params_factory = default_params_factory

    def fit(self, data: np.ndarray, params: Optional[ConanFitParams] = None):
        params = params or self._default_params_factory.create()
        params_dict = {
            'baseline': params.baseline,
        }
        cfut = self._executor.submit(contact_angle_fit, data, **params_dict)
        fut = asyncio.wrap_future(cfut, loop=asyncio.get_event_loop())
        return fut

    def destroy(self) -> None:
        self._executor.shutdown()
