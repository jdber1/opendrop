import numpy as np
from typing_extensions import Protocol


Image = np.ndarray


class Destroyable(Protocol):
    def destroy(self) -> None:
        """Destroy this object"""
