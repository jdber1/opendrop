from abc import abstractmethod

import numpy as np


class ImageFilter:
    @abstractmethod
    def apply(self, image: np.ndarray) -> np.ndarray:
        pass
