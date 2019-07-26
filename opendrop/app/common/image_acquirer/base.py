import math
from abc import ABC, abstractmethod
from typing import Sequence, Optional, Tuple

import numpy as np


class ImageAcquirer(ABC):
    @abstractmethod
    def acquire_images(self) -> Sequence['InputImage']:
        """Implementation of acquire_images()"""

    @abstractmethod
    def get_image_size_hint(self) -> Optional[Tuple[int, int]]:
        """Implementation of get_image_size_hint()"""

    def destroy(self) -> None:
        """Destroy this object, perform any necessary cleanup tasks."""


class InputImage(ABC):
    est_ready = math.nan
    is_replicated = False

    @abstractmethod
    async def read(self) -> Tuple[np.ndarray, float]:
        """Return the image and timestamp."""

    def cancel(self) -> None:
        pass
