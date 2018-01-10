from typing import Any, Generic, TypeVar, List

import numpy as np
import time

from opendrop.image_filter.bases import ImageFilter

T = TypeVar('T')


class TimestampContainer(Generic[T]):
    def __init__(self, value: T) -> None:
        self.value = value  # type: T
        self.timestamp = time.time()  # type: float


class ImageFilterGroup(ImageFilter):
    """Filters sorted by z_index (highest applied first, then lowest) and if equal z_index, sort by timestamp (earliest
    added applied first, then latest). If filter has no z_index attribute, then z_index is set to 0"""
    def __init__(self) -> None:
        self._filters = []  # type: List[TimestampContainer[ImageFilter]]

    def apply(self, image: np.ndarray) -> np.ndarray:
        for f in map(lambda c: c.value, self._filters):
            image = f.apply(image)

        return image

    def add(self, image_filter: ImageFilter) -> None:
        self._filters.append(TimestampContainer(image_filter))

        self._resort()

    def remove(self, image_filter: ImageFilter) -> None:
        for c in list(self._filters):
            if c.value == image_filter:
                self._filters.remove(c)

                break

    def _resort(self) -> None:
        self._filters.sort(key=lambda c: (-c.value.z_index if hasattr(c.value, 'z_index') else 0, c.timestamp))
