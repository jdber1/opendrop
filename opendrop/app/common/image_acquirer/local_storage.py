from pathlib import Path
from typing import Union, Sequence, MutableSequence

import cv2
import numpy as np

from opendrop.utility.bindable import BoxBindable
from .image_sequence import ImageSequenceAcquirer


class LocalStorageAcquirer(ImageSequenceAcquirer):
    IS_REPLICATED = True

    def __init__(self) -> None:
        super().__init__()
        self.bn_last_loaded_paths = BoxBindable(tuple())  # type: BoxBindable[Sequence[Path]]

    def load_image_paths(self, image_paths: Sequence[Union[Path, str]]) -> None:
        # Sort image paths in lexicographic order, and ignore paths to directories.
        image_paths = sorted([p for p in map(Path, image_paths) if not p.is_dir()])

        images = []  # type: MutableSequence[np.ndarray]
        for image_path in image_paths:
            image = cv2.imread(str(image_path))
            if image is None:
                raise ValueError(
                    "Failed to load image from path '{}'"
                    .format(image_path)
                )

            # OpenCV loads images in BGR mode, but the rest of the app works with images in RGB, so convert the read
            # image appropriately.
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            images.append(image)

        self.bn_images.set(images)
        self.bn_last_loaded_paths.set(tuple(image_paths))

