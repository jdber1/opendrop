import asyncio
from enum import IntEnum
import math
import time
from typing import Optional

from injector import inject, Injector
from gi.repository import GObject

import numpy as np

from opendrop.geometry import Vector2, Rect2, Line2
from opendrop.app.common.services.acquisition import InputImage

from .params import ConanParams, ConanParamsFactory
from .features import ConanFeatures, ConanFeaturesService
from .conan import ConanFitResult, ConanFitService


class ConanAnalysisStatus(IntEnum):
    WAITING_FOR_IMAGE = 1
    EXTRACTING_FEATURES = 2
    FITTING = 3

    TERMINAL = 8
    FINISHED = TERMINAL + 1
    CANCELLED = TERMINAL + 2


class ConanAnalysisService:
    @inject
    def __init__(self, *, params_factory: ConanParamsFactory, injector: Injector) -> None:
        self._params_factory = params_factory
        self._injector = injector

    def analyse(self, source: InputImage) -> 'ConanAnalysisJob':
        return self._injector.create_object(
            ConanAnalysisJob, {
                'source': source,
                'params': self._params_factory.create()
            },
        )


class ConanAnalysisJob(GObject.GObject):
    @inject
    def __init__(
            self,
            source: InputImage,
            params: ConanParams,
            *,
            features_service: ConanFeaturesService,
            cafit_service: ConanFitService,
    ) -> None:
        super().__init__()
        self._loop = asyncio.get_event_loop()

        self._source = source

        self._params = params
        self._features_service = features_service
        self._cafit_service = cafit_service

        self._image = None
        self._timestamp = None

        # A bit of a hack for the UI, just set timestamp to how much longer until source is ready.
        if math.isfinite(source.est_ready):
            self._timestamp = source.est_ready - time.time()

        # Parameters
        self._baseline = params.baseline
        self._inverted = params.inverted
        self._roi = params.roi

        # Features
        self._drop_points = None

        # Fit results
        self._left_contact = None
        self._right_contact = None
        self._left_angle = None
        self._right_angle = None
        self._left_curvature = None
        self._right_curvature = None
        self._left_arc_center = None
        self._right_arc_center = None
        self._left_residuals = None
        self._right_residuals = None
        self._left_mask = None
        self._right_mask = None

        self._status = ConanAnalysisStatus.WAITING_FOR_IMAGE
        self._job_start = time.time()
        self._job_end = None
        self._features = None
        self._cafit = None

        self._loop.create_task(source.read()).add_done_callback(self._source_read_done)

    def _source_read_done(self, fut: asyncio.Future) -> None:
        if fut.cancelled():
            self.cancel()
            return
        
        if self.done():
            return

        image, timestamp = fut.result()
        self._image_ready(image, timestamp)

    def _image_ready(self, image: np.ndarray, timestamp: float) -> None:
        self._image = image
        self._timestamp = timestamp

        self._features = self._features_service.extract(image, self._params)
        self._features.add_done_callback(self._features_done)

        self.status = ConanAnalysisStatus.EXTRACTING_FEATURES

    def _features_done(self, fut: asyncio.Future) -> None:
        if fut.cancelled():
            self.cancel()
        
        if self.done():
            return

        features: ConanFeatures = fut.result()
        self.drop_points = features.drop_points

        self._cafit = self._cafit_service.fit(features.drop_points, self._params)
        self._cafit.add_done_callback(self._cafit_done)

        self.status = ConanAnalysisStatus.FITTING

    def _cafit_done(self, fut: asyncio.Future) -> None:
        if fut.cancelled():
            self.cancel()
        
        if self.done():
            return

        result: ConanFitResult = fut.result()
        self.left_contact = result.left_contact
        self.right_contact = result.right_contact
        self.left_angle = result.left_angle
        self.right_angle = result.right_angle
        self.left_curvature = result.left_curvature
        self.right_curvature = result.right_curvature
        self.left_arc_center = result.left_arc_center
        self.right_arc_center = result.right_arc_center
        self.left_arclengths = result.left_arclengths
        self.right_arclengths = result.right_arclengths
        self.left_residuals = result.left_residuals
        self.right_residuals = result.right_residuals
        self.left_mask = result.left_mask
        self.right_mask = result.right_mask

        self.status = ConanAnalysisStatus.FINISHED
        self.job_end = time.time()

    def cancel(self) -> None:
        if self.done():
            # Analysis is already done.
            return

        if self.status is ConanAnalysisStatus.WAITING_FOR_IMAGE:
            self._source.cancel()

        if self._features is not None:
            self._features.cancel()

        if self._cafit is not None:
            self._cafit.cancel()

        self.status = ConanAnalysisStatus.CANCELLED

    @GObject.Property
    def status(self) -> ConanAnalysisStatus:
        return self._status
    
    @status.setter
    def status(self, status: ConanAnalysisStatus) -> None:
        self._status = status

    @GObject.Property
    def job_start(self) -> float:
        return self._job_start

    @GObject.Property
    def job_end(self) -> Optional[float]:
        return self._job_end

    @job_end.setter
    def job_end(self, timestamp: float) -> None:
        self._job_end = timestamp

    @GObject.Property
    def image(self) -> Optional[np.ndarray]:
        return self._image

    @image.setter
    def image(self, image: np.ndarray) -> None:
        self._image = image
    
    @GObject.Property
    def image_replicated(self) -> bool:
        return self._source.is_replicated

    @GObject.Property
    def timestamp(self) -> Optional[float]:
        return self._timestamp
    
    @timestamp.setter
    def timestamp(self, timestamp: float) -> None:
        self._timestamp = timestamp

    @GObject.Property
    def baseline(self) -> Optional[Line2]:
        return self._baseline
    
    @baseline.setter
    def baseline(self, line: Line2) -> None:
        self._baseline = line

    @GObject.Property
    def inverted(self) -> bool:
        return self._inverted
    
    @inverted.setter
    def inverted(self, value: bool) -> None:
        self._inverted = value

    @GObject.Property
    def roi(self) -> Optional[Rect2[int]]:
        return self._roi

    @roi.setter
    def roi(self, region: Rect2[int]) -> None:
        self._roi = region

    @GObject.Property
    def drop_points(self) -> Optional[np.ndarray]:
        return self._drop_points

    @drop_points.setter
    def drop_points(self, points: np.ndarray) -> None:
        self._drop_points = points

    @GObject.Property
    def left_contact(self) -> Optional[Vector2[float]]:
        return self._left_contact

    @left_contact.setter
    def left_contact(self, point: Optional[Vector2[float]]) -> None:
        self._left_contact = point

    @GObject.Property
    def right_contact(self) -> Optional[Vector2[float]]:
        return self._right_contact

    @right_contact.setter
    def right_contact(self, point: Optional[Vector2[float]]) -> None:
        self._right_contact = point

    @GObject.Property
    def left_angle(self) -> Optional[float]:
        return self._left_angle

    @left_angle.setter
    def left_angle(self, angle: Optional[float]) -> None:
        self._left_angle = angle

    @GObject.Property
    def right_angle(self) -> Optional[float]:
        return self._right_angle

    @right_angle.setter
    def right_angle(self, angle: Optional[float]) -> None:
        self._right_angle = angle

    @GObject.Property
    def left_curvature(self) -> Optional[float]:
        return self._left_curvature

    @left_curvature.setter
    def left_curvature(self, curvature: Optional[float]) -> None:
        self._left_curvature = curvature

    @GObject.Property
    def right_curvature(self) -> Optional[float]:
        return self._right_curvature

    @right_curvature.setter
    def right_curvature(self, curvature: Optional[float]) -> None:
        self._right_curvature = curvature

    @GObject.Property
    def left_arc_center(self) -> Optional[Vector2[float]]:
        return self._left_arc_center

    @left_arc_center.setter
    def left_arc_center(self, center: Optional[Vector2[float]]) -> None:
        self._left_arc_center = center

    @GObject.Property
    def right_arc_center(self) -> Optional[Vector2[float]]:
        return self._right_arc_center

    @right_arc_center.setter
    def right_arc_center(self, center: Optional[Vector2[float]]) -> None:
        self._right_arc_center = center

    @GObject.Property
    def left_arclengths(self) -> Optional[np.ndarray]:
        return self._left_arclengths

    @left_arclengths.setter
    def left_arclengths(self, arclengths: Optional[np.ndarray]) -> None:
        self._left_arclengths = arclengths

    @GObject.Property
    def right_arclengths(self) -> Optional[np.ndarray]:
        return self._right_arclengths

    @right_arclengths.setter
    def right_arclengths(self, arclengths: Optional[np.ndarray]) -> None:
        self._right_arclengths = arclengths

    @GObject.Property
    def left_residuals(self) -> Optional[np.ndarray]:
        return self._left_residuals

    @left_residuals.setter
    def left_residuals(self, residuals: Optional[np.ndarray]) -> None:
        self._left_residuals = residuals

    @GObject.Property
    def right_residuals(self) -> Optional[np.ndarray]:
        return self._right_residuals

    @right_residuals.setter
    def right_residuals(self, residuals: Optional[np.ndarray]) -> None:
        self._right_residuals = residuals

    @GObject.Property
    def left_mask(self) -> Optional[np.ndarray]:
        return self._left_mask

    @left_mask.setter
    def left_mask(self, mask: Optional[np.ndarray]) -> None:
        self._left_mask = mask

    @GObject.Property
    def right_mask(self) -> Optional[np.ndarray]:
        return self._right_mask

    @right_mask.setter
    def right_mask(self, mask: Optional[np.ndarray]) -> None:
        self._right_mask = mask

    def done(self) -> bool:
        return (self._status & ConanAnalysisStatus.TERMINAL) != 0

    def cancelled(self) -> bool:
        return self._status is ConanAnalysisStatus.CANCELLED
