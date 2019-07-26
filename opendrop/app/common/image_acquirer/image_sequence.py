from typing import Sequence, Tuple, Optional

import numpy as np

from opendrop.utility.bindable import Bindable, BoxBindable
from .base import ImageAcquirer, InputImage


class ImageSequenceAcquirer(ImageAcquirer):
    IS_REPLICATED = False

    def __init__(self) -> None:
        self.bn_images = BoxBindable(tuple())  # type: Bindable[Sequence[np.ndarray]]

        self.bn_frame_interval = BoxBindable(None)  # type: Bindable[Optional[int]]

    def acquire_images(self) -> Sequence[InputImage]:
        images = self.bn_images.get()
        if len(images) == 0:
            raise ValueError("'_images' can't be empty")

        frame_interval = self.bn_frame_interval.get()
        if frame_interval is None or frame_interval <= 0:
            if len(images) == 1:
                # Since only one image, we don't care about the frame_interval.
                frame_interval = 0
            else:
                raise ValueError(
                    "'frame_interval' must be > 0 and not None, currently: '{}'"
                    .format(frame_interval)
                )

        input_images = []

        for i, img in enumerate(images):
            input_image = _BaseImageSequenceInputImage(
                image=img,
                timestamp=i * frame_interval
            )
            input_image.is_replicated = self.IS_REPLICATED
            input_images.append(input_image)

        return input_images

    def get_image_size_hint(self) -> Optional[Tuple[int, int]]:
        images = self.bn_images.get()
        if images is None or len(images) == 0:
            return None

        first_image = images[0]
        return first_image.shape[1::-1]


class _BaseImageSequenceInputImage(InputImage):
    def __init__(self, image: np.ndarray, timestamp: float) -> None:
        self._image = image
        self._timestamp = timestamp

    async def read(self) -> Tuple[np.ndarray, float]:
        return self._image, self._timestamp
