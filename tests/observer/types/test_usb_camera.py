# Make sure the webcam scene isn't changing too quickly while this test is running, or the results may be incorrect.
import asyncio

import cv2
import numpy as np
import pytest
import time
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


def camera_capture_test_image(camera_index=TEST_CAMERA_INDEX):
    vc = cv2.VideoCapture(camera_index)

    if not vc.isOpened():
        raise ValueError('Failed to capture test image')

    # Consume the few images since for some cameras they are unusually dark
    for i in range(5):
        vc.read()

    try:
        success, image = None, None

        while not success:
            success, image = vc.read()

        return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    finally:
        vc.release()


def image_similar(img0, img1):  # compares histograms to check for image similarity
    # Using user verification
    cv2.imshow('Image comparison', np.concatenate((img0, img1), axis=1))
    cv2.waitKey(0)

    return True

    # # Comparing histograms to verify similarity
    # hist0 = cv2.calcHist([img0], mask=None, channels=[0, 1, 2], histSize=[8, 8, 8], ranges=[0, 256, 0, 256, 0, 256])
    # hist0 = cv2.normalize(hist0, dst=hist0).flatten()
    #
    # hist1 = cv2.calcHist([img1], mask=None, channels=[0, 1, 2], histSize=[8, 8, 8], ranges=[0, 256, 0, 256, 0, 256])
    # hist1 = cv2.normalize(hist1, dst=hist0).flatten()
    #
    # return cv2.compareHist(hist0, hist1,  method=cv2.HISTCMP_CORREL) > CORREL_MIN


@pytest.mark.skipif(
    not TEST_CAMERA_EXISTS,
    reason='No camera found on index {}'.format(TEST_CAMERA_INDEX)
)
class TestUSBCamera:
    def setup(self):
        # Need to capture the reference image from the camera before USBCamera is initialised otherwise we might not be
        # able to create a VideoCapture as the resource will be busy.
        self.truth_image = camera_capture_test_image()

        self.cam = USBCamera(TEST_CAMERA_INDEX)

    def test_capture(self):
        test_img = self.cam.capture()

        assert image_similar(self.truth_image, test_img)

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
        self.truth_image = camera_capture_test_image()

        self.provider = USBCameraObserverProvider()

    # If `timelapse()` captures the correct images, then we assume that `preview()` does as well
    @pytest.mark.asyncio
    async def test_timelapse(self):
        cam_observer = self.provider.provide(TEST_CAMERA_INDEX)

        [observation] = cam_observer.timelapse([0])

        test_img = await observation

        assert image_similar(self.truth_image, test_img)
