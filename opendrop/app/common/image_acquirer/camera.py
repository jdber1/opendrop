import asyncio
import math
import time
from abc import ABC, abstractmethod
from typing import Sequence, Tuple, Optional

import numpy as np

from opendrop.utility.bindable import Bindable, BoxBindable
from .base import ImageAcquirer, InputImage


class CameraAcquirer(ImageAcquirer):
    def __init__(self) -> None:
        self._loop = asyncio.get_event_loop()

        self.bn_camera = BoxBindable(None)  # type: Bindable[Optional[Camera]]

        self.bn_num_frames = BoxBindable(1)
        self.bn_frame_interval = BoxBindable(None)  # type: Bindable[Optional[float]]

    def acquire_images(self) -> Sequence[InputImage]:
        camera = self.bn_camera.get()

        if camera is None:
            raise ValueError("'camera' can't be None")

        num_frames = self.bn_num_frames.get()

        if num_frames is None or num_frames <= 0:
            raise ValueError(
                "'num_frames' must be > 0 and not None, currently: '{}'"
                .format(num_frames)
            )

        frame_interval = self.bn_frame_interval.get()

        if frame_interval is None or frame_interval <= 0:
            if num_frames == 1:
                frame_interval = 0
            else:
                raise ValueError(
                    "'frame_interval' must be > 0 and not None, currently: '{}'"
                    .format(frame_interval)
                )

        input_images = []

        for i in range(num_frames):
            capture_delay = i * frame_interval

            input_image = _BaseCameraInputImage(
                camera=camera,
                delay=capture_delay,
                first_image=input_images[0] if input_images else None,
                loop=self._loop,
            )

            input_images.append(input_image)

        return input_images

    def get_image_size_hint(self) -> Optional[Tuple[int, int]]:
        camera = self.bn_camera.get()
        if camera is None:
            return

        return camera.get_image_size_hint()


class _BaseCameraInputImage(InputImage):
    def __init__(self, camera: 'Camera', delay: float, first_image: Optional['_BaseCameraInputImage'] = None, *,
                 loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

        self._first_image = first_image

        self._read_fut = self._loop.create_future()

        self._camera = camera
        self._do_capture_handle = self._loop.call_later(delay=delay, callback=self._do_capture)

        self.capture_time = math.nan

        self.est_ready = time.time() + delay

    def _do_capture(self) -> None:
        image = self._camera.capture()
        self._capture_time = time.time()

        if self._first_image is not None:
            timestamp = self._capture_time - self._first_image._capture_time
        else:
            timestamp = 0

        timestamp = round(timestamp, 1)

        self._read_fut.set_result(
            (image, timestamp)
        )

    async def read(self) -> Tuple[np.ndarray, float]:
        return await self._read_fut

    def cancel(self) -> None:
        self._do_capture_handle.cancel()
        self._read_fut.cancel()


class Camera(ABC):
    @abstractmethod
    def capture(self) -> np.ndarray:
        """Return the captured image."""

    @abstractmethod
    def get_image_size_hint(self) -> Optional[Tuple[int, int]]:
        """Implementation of get_image_size_hint()"""


class CameraCaptureError(Exception):
    """Raised when a camera capture fails."""
