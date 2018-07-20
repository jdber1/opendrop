import asyncio
import os
from unittest.mock import Mock

import cv2
import numpy as np
import pytest
from pytest import raises

from opendrop.observer.types.image_slideshow import ImageSlideshowObserver, ImageSlideshowObserverPreview
from tests import samples


def test_stub():
    pass


SAMPLES_DIR = os.path.dirname(samples.__file__)

IMAGE_PATHS = [os.path.join(SAMPLES_DIR, *image_path) for image_path in (
    ('images', 'image0.png'),
    ('images', 'image1.png'),
    ('images', 'image2.png'),
    ('images', 'image3.png'),
    ('images', 'image4.png')
)]

IMAGES = [cv2.imread(image_path) for image_path in IMAGE_PATHS]
IMAGES = [cv2.cvtColor(image, cv2.COLOR_BGR2RGB) for image in IMAGES]

IMAGE_INTERVAL = 10

IMAGE_TIMESTAMPS = np.arange(len(IMAGE_PATHS)) * IMAGE_INTERVAL


class TestImageSlideshowObserver:
    def setup(self):
        self.observer = ImageSlideshowObserver(IMAGE_PATHS, timestamps=IMAGE_TIMESTAMPS)

    def test_timestamps(self):
        timestamps = range(len(IMAGE_PATHS))

        self.observer.timestamps = timestamps

        assert self.observer.timestamps == timestamps

        # Test that setting `timestamps` to an array with length that does not correspond to length of image paths,
        # raises an exception.
        with raises(ValueError):
            self.observer.timestamps = range(len(IMAGE_PATHS) + 1)

    @pytest.mark.asyncio
    async def test_timelapse(self):
        noise = np.random.uniform(-0.4, 0.4, len(IMAGE_TIMESTAMPS)) * IMAGE_INTERVAL

        # Add noise to the timestamps to test using timelapse with inexact timestamps
        observations = self.observer.timelapse(self.observer.timestamps + noise)

        for o, target in zip(observations, IMAGES):
            assert (await o == target).all()

    def test_create_with_zero_paths(self):
        with raises(ValueError):
            ImageSlideshowObserver(image_paths=[], timestamps=[])


class TestImageSlideshowObserverPreview:
    def setup(self):
        self.observer = ImageSlideshowObserver(IMAGE_PATHS, timestamps=IMAGE_TIMESTAMPS)
        self.preview = ImageSlideshowObserverPreview(self.observer)

    def test_num_images(self):
        assert self.preview.num_images == len(IMAGE_PATHS)

    @pytest.mark.asyncio
    async def test_show(self):
        IMAGE_INDEX_TO_SHOW = 0

        cb = Mock()

        self.preview.on_update.connect(cb)

        self.preview.show(IMAGE_INDEX_TO_SHOW)

        await asyncio.sleep(0.001)

        assert (cb.call_args[0] == IMAGES[IMAGE_INDEX_TO_SHOW]).all()

    def teardown(self):
        self.preview.close()


def test_init_with_invalid_paths():
    with raises(ValueError):
        ImageSlideshowObserver(['nonsense'], timestamps=[1])


def test_init_with_invalid_timestamps():
    with raises(ValueError):
        ImageSlideshowObserver(IMAGE_PATHS, timestamps=range(len(IMAGE_TIMESTAMPS) + 1))
