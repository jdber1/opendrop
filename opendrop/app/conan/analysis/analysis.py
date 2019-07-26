import asyncio
import math
import time
from asyncio import Future
from enum import Enum
from typing import Callable, Optional

import numpy as np

from opendrop.app.common.image_acquirer import InputImage
from opendrop.utility.bindable import AccessorBindable, BoxBindable, Bindable
from opendrop.utility.geometry import Vector2
from .contact_angle import ContactAngleCalculator
from .features import FeatureExtractor


# Classes

class ConanAnalysis:
    class Status(Enum):
        WAITING_FOR_IMAGE = ('Waiting for image', False)
        FITTING = ('Fitting', False)
        FINISHED = ('Finished', True)
        CANCELLED = ('Cancelled', True)

        def __init__(self, display_name: str, is_terminal: bool) -> None:
            self.display_name = display_name
            self.is_terminal = is_terminal

        def __str__(self) -> str:
            return self.display_name

    def __init__(
            self,
            input_image: InputImage,
            do_extract_features: Callable[[Bindable[np.ndarray]], FeatureExtractor],
            do_calculate_conan: Callable[[FeatureExtractor], ContactAngleCalculator],
    ) -> None:
        self._loop = asyncio.get_event_loop()

        self._time_start = time.time()
        self._time_end = math.nan

        self._input_image = input_image
        self._do_extract_features = do_extract_features
        self._do_calculate_conan = do_calculate_conan

        self._status = self.Status.WAITING_FOR_IMAGE

        self.bn_status = AccessorBindable(
            getter=self._get_status,
            setter=self._set_status,
        )

        self._image = None  # type: Optional[np.ndarray]
        # The time (in Unix time) that the image was captured.
        self._image_timestamp = math.nan  # type: float

        self._extracted_features = None  # type: Optional[FeatureExtractor]
        self._calculated_conan = None  # type: Optional[ContactAngleCalculator]

        self.bn_image = AccessorBindable(self._get_image)
        self.bn_image_timestamp = AccessorBindable(self._get_image_timestamp)

        # Attributes from ContactAngleCalculator
        self.bn_left_angle = BoxBindable(math.nan)
        self.bn_left_tangent = BoxBindable(np.poly1d((math.nan, math.nan)))
        self.bn_left_point = BoxBindable(Vector2(math.nan, math.nan))
        self.bn_right_angle = BoxBindable(math.nan)
        self.bn_right_tangent = BoxBindable(np.poly1d((math.nan, math.nan)))
        self.bn_right_point = BoxBindable(Vector2(math.nan, math.nan))

        self.bn_surface_line = BoxBindable(None)

        # Attributes from FeatureExtractor
        self.bn_drop_region = BoxBindable(None)
        self.bn_drop_profile_extract = BoxBindable(None)

        # Log
        self.bn_is_done = AccessorBindable(getter=self._get_is_done)
        self.bn_is_cancelled = AccessorBindable(getter=self._get_is_cancelled)
        self.bn_progress = AccessorBindable(self._get_progress)
        self.bn_time_start = AccessorBindable(self._get_time_start)
        self.bn_time_est_complete = AccessorBindable(self._get_time_est_complete)

        self.bn_status.on_changed.connect(self.bn_is_done.poke)
        self.bn_status.on_changed.connect(self.bn_progress.poke)

        self._loop.create_task(self._input_image.read()).add_done_callback(self._hdl_input_image_read)

    def _hdl_input_image_read(self, read_task: Future) -> None:
        if read_task.cancelled():
            self.cancel()
            return

        if self.bn_is_done.get():
            return

        image, image_timestamp = read_task.result()
        self._start_fit(image, image_timestamp)

    def _start_fit(self, image: np.ndarray, image_timestamp: float) -> None:
        assert self._image is None

        self._image = image
        self._image_timestamp = image_timestamp

        # Set given image to be readonly to prevent introducing some accidental bugs.
        self._image.flags.writeable = False

        extracted_features = self._do_extract_features(BoxBindable(self._image))
        calculated_conan = self._do_calculate_conan(extracted_features)

        self._extracted_features = extracted_features
        self._calculated_conan = calculated_conan

        self._bind_fit()

        self.bn_image.poke()
        self.bn_image_timestamp.poke()

        self.bn_status.set(self.Status.FINISHED)

    def _bind_fit(self) -> None:
        # Bind extracted features attributes
        self._extracted_features.bn_drop_profile_px.bind(
            self.bn_drop_profile_extract
        )
        self._extracted_features.params.bn_drop_region_px.bind(
            self.bn_drop_region
        )

        # Bind contact angle attributes
        self._calculated_conan.bn_left_angle.bind(
            self.bn_left_angle
        )
        self._calculated_conan.bn_left_tangent.bind(
            self.bn_left_tangent
        )
        self._calculated_conan.bn_left_point.bind(
            self.bn_left_point
        )
        self._calculated_conan.bn_right_angle.bind(
            self.bn_right_angle
        )
        self._calculated_conan.bn_right_tangent.bind(
            self.bn_right_tangent
        )
        self._calculated_conan.bn_right_point.bind(
            self.bn_right_point
        )
        self._calculated_conan.params.bn_surface_line_px.bind(
            self.bn_surface_line
        )

    def cancel(self) -> None:
        if self.bn_status.get().is_terminal:
            # This is already at the end of its life.
            return

        if self.bn_status.get() is self.Status.WAITING_FOR_IMAGE:
            self._input_image.cancel()

        self.bn_status.set(self.Status.CANCELLED)

    def _get_status(self) -> Status:
        return self._status

    def _set_status(self, new_status: Status) -> None:
        self._status = new_status
        self.bn_is_cancelled.poke()

        if new_status.is_terminal:
            self._time_end = time.time()

    def _get_image(self) -> Optional[np.ndarray]:
        return self._image

    def _get_image_timestamp(self) -> float:
        return self._image_timestamp

    def _get_is_done(self) -> bool:
        return self.bn_status.get().is_terminal

    def _get_is_cancelled(self) -> bool:
        return self.bn_status.get() is self.Status.CANCELLED

    def _get_progress(self) -> float:
        if self.bn_is_done.get():
            return 1
        else:
            return 0

    def _get_time_start(self) -> float:
        return self._time_start

    def _get_time_est_complete(self) -> float:
        if self._input_image is None:
            return math.nan

        return self._input_image.est_ready

    def calculate_time_elapsed(self) -> float:
        time_start = self._time_start

        if math.isfinite(self._time_end):
            time_elapsed = self._time_end - time_start
        else:
            time_now = time.time()
            time_elapsed = time_now - time_start

        return time_elapsed

    def calculate_time_remaining(self) -> float:
        if self.bn_is_done.get():
            return 0

        time_est_complete = self.bn_time_est_complete.get()
        time_now = time.time()
        time_remaining = time_est_complete - time_now

        return time_remaining

    @property
    def is_image_replicated(self) -> bool:
        return self._input_image.is_replicated
