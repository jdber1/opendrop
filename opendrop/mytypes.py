import numpy as np

Image = np.ndarray


class Destroyable:
    def destroy(self) -> None:
        """Destroy this object"""
