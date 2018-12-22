from asyncio import Future
from typing import Tuple, List


class ImageAcquisition:
    def acquire_images(self) -> Tuple[List[Future], List[float]]:
        """Return a tuple, with the first element being a list of futures which will be resolved to each image, and the
        second element being a list of estimated timestamps for when the futures will be resolved."""
