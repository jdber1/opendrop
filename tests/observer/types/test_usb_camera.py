# Make sure the webcam scene isn't changing too quickly while this test is running, or the results may be incorrect.
import asyncio

import cv2
import pytest
from pytest import raises

from opendrop.observer.types.usb_camera import USBCamera, USBCameraObserverProvider

TEST_CAMERA_INDEX = 0
CORREL_MIN = 0.99


def check_camera_index_exists(camera_index):
    vc = cv2.VideoCapture(camera_index)

    success = vc.isOpened()

    vc.release()

    return success


TEST_CAMERA_EXISTS = check_camera_index_exists(TEST_CAMERA_INDEX)


def test_camera_capture(camera_index=TEST_CAMERA_INDEX):
    vc = cv2.VideoCapture(camera_index)

    while not vc.isOpened():
        pass

    while True:
        success, image = vc.read()

        if success:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            return image


def image_similar(img0, img1):  # compares histograms to check for image similarity
    hist0 = cv2.calcHist([img0], mask=None, channels=[0, 1, 2], histSize=[8, 8, 8], ranges=[0, 256, 0, 256, 0, 256])
    hist0 = cv2.normalize(hist0, dst=hist0).flatten()

    hist1 = cv2.calcHist([img1], mask=None, channels=[0, 1, 2], histSize=[8, 8, 8], ranges=[0, 256, 0, 256, 0, 256])
    hist1 = cv2.normalize(hist1, dst=hist0).flatten()

    return cv2.compareHist(hist0, hist1,  method=cv2.HISTCMP_CORREL) > CORREL_MIN


@pytest.mark.skipif(
    not TEST_CAMERA_EXISTS,
    reason='No camera found on index {}'.format(TEST_CAMERA_INDEX)
)
class TestUSBCamera:
    def setup(self):
        self.cam = USBCamera(TEST_CAMERA_INDEX)

    def test_capture(self):
        target_img = test_camera_capture()
        test_img = self.cam.capture()

        assert image_similar(target_img, test_img)

    def test_capture_after_teardown(self):
        self.cam.teardown()

        # Make sure that trying to capture after teardown raises a `ValueError`
        with raises(ValueError):
            self.cam.capture()

    def teardown(self):
        self.cam.teardown()


@pytest.mark.skipif(
    not TEST_CAMERA_EXISTS,
    reason='No camera found on index {}'.format(TEST_CAMERA_INDEX)
)
class TestUSBCameraProvider:
    def setup(self):
        self.provider = USBCameraObserverProvider()

    # If `timelapse()` captures the correct images, then we assume that `preview()` does as well
    @pytest.mark.asyncio
    async def test_timelapse(self):
        cam_observer = self.provider.provide(TEST_CAMERA_INDEX)

        [observation] = cam_observer.timelapse([0])

        target_img = test_camera_capture()
        test_img = await observation

        assert image_similar(target_img, test_img)
