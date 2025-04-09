from abc import abstractmethod
import asyncio
from concurrent.futures.process import ProcessPoolExecutor
from typing import Optional, Protocol

from gi.repository import GObject
from injector import inject
import numpy as np

from opendrop.geometry import Line2, Rect2
from opendrop.features import extract_contact_angle_features, ContactAngleFeatures as ConanFeatures

from .params import ConanParamsFactory


__all__ = (
    'ConanFeatures',
    'ConanFeaturesService',
)


class ConanFeaturesParams(Protocol):
    @property
    @abstractmethod
    def baseline(self) -> Optional[Line2]: ...

    @property
    @abstractmethod
    def thresh(self) -> float: ...

    @property
    @abstractmethod
    def roi(self) -> Optional[Line2]: ...

    @property
    @abstractmethod
    def inverted(self) -> bool: ...


class ConanFeaturesService:
    @inject
    def __init__(self, default_params_factory: ConanParamsFactory) -> None:
        self._executor = ProcessPoolExecutor(max_workers=1)
        self._default_params_factory = default_params_factory

    def extract(
            self,
            image: np.ndarray,
            params: Optional[ConanFeaturesParams] = None,
            *,
            labels: bool = False
    ) -> asyncio.Future:
        params = params or self._default_params_factory.create()
        params_dict = {
            'baseline': params.baseline,
            'inverted': params.inverted,
            'thresh': params.thresh,
            'roi': params.roi,
            'labels': labels,
        }
        cfut = self._executor.submit(extract_contact_angle_features, image, **params_dict)
        fut = asyncio.wrap_future(cfut, loop=asyncio.get_event_loop())
        return fut

    def destroy(self) -> None:
        self._executor.shutdown()
