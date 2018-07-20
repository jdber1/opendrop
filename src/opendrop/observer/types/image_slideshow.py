from typing import List, Sequence, Optional

import cv2
import numpy as np

from opendrop.observer import types
from opendrop.observer.bases import Observer, Observation, ObserverPreview, ObserverProvider, ObserverType


def get_invalid_image_paths(image_paths: List[str]) -> Optional[str]:
    for image_path in image_paths:
        if cv2.imread(image_path) is None:
            return image_path


class ImageSlideshowObserver(Observer):
    def __init__(self, image_paths: List[str], timestamps: Sequence[float]) -> None:
        if len(image_paths) == 0:
            raise ValueError(
                'image_paths is empty'
            )

        invalid_image_path = get_invalid_image_paths(image_paths)
        if invalid_image_path is not None :
            raise ValueError(
                '{!r} is not a valid image path'.format(invalid_image_path)
            )

        self.image_paths = image_paths  # type: List[str]
        self.timestamps = timestamps

    @property
    def timestamps(self) -> Sequence[float]:
        return self._timestamps

    @timestamps.setter
    def timestamps(self, value: Sequence[float]) -> None:
        if len(value) != len(self.image_paths):
            raise ValueError(
                'Length of timestamps ({}) does not match length of images ({})'
                .format(len(self.image_paths), len(value))
            )

        self._timestamps = value

    @property
    def num_images(self) -> int:
        return len(self.image_paths)

    def get_image(self, index: Optional[int] = None, *, timestamp: Optional[float] = None) -> np.ndarray:
        index = index if index is not None else np.abs(np.array(self.timestamps) - timestamp).argmin()

        image_path = self.image_paths[index]

        image = cv2.imread(image_path)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        return image

    # add to doc: If timestamps don't match exactly to the images timestamps, the image with the closest timestamp is
    # used to represent the observation.
    def timelapse(self, timestamps: Sequence[float]) -> List['Observation']:
        observations = []

        for image_path, t in zip(self.image_paths, timestamps):
            new_observation = Observation()  # type: Observation
            new_observation.load(self.get_image(timestamp=t), t)

            observations.append(new_observation)

        return observations

    def preview(self) -> 'ImageSlideshowObserverPreview':
        return ImageSlideshowObserverPreview(self)


class ImageSlideshowObserverPreview(ObserverPreview):
    def __init__(self, observer: ImageSlideshowObserver):
        super().__init__(observer)

        self._index = 0
        self._observer = observer

    @property
    def buffer(self) -> np.ndarray:
        return self._observer.get_image(self._index)

    @property
    def num_images(self) -> int:
        return self._observer.num_images

    def show(self, index: int):
        self._index = index
        self.on_changed.fire()

    def close(self):
        # No need to do any clean up
        pass


class ImageSlideshowObserverProvider(ObserverProvider):
    def provide(self, image_paths: List[str], timestamps: Sequence[float]) -> ImageSlideshowObserver:
        return ImageSlideshowObserver(image_paths, timestamps)


types.IMAGE_SLIDESHOW = ObserverType('Images', ImageSlideshowObserverProvider())
