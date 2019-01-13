import asyncio
import time
from itertools import zip_longest
from pathlib import Path
from unittest.mock import Mock

import cv2
import numpy as np
import pytest

from opendrop.app.common.model.image_acquisition.default_types import \
    BaseImageSequenceImageAcquisitionImpl, LocalImagesImageAcquisitionImpl, BaseCameraImageAcquisitionImpl, Camera, \
    CameraCaptureError
from tests import samples

EPSILON_FOR_TIME = 0.1

SAMPLE_IMAGES_DIR = Path(samples.__file__).parent/'images'

MOCK_IMAGE_0 = np.zeros((16, 16, 3))
MOCK_IMAGE_1 = MOCK_IMAGE_0.copy()
MOCK_IMAGE_1[0, 0, 0] = 1
MOCK_IMAGE_2 = MOCK_IMAGE_0.copy()
MOCK_IMAGE_2[0, 0, 0] = 1


async def _test_acquire_images_ret_val_images(acquire_images_ret_val, expected_imgs):
    for fut, est, expected_img in zip_longest(*acquire_images_ret_val, expected_imgs):
        img, img_timestamp = await fut
        assert (img == expected_img).all()


async def _test_acquire_images_ret_val_timestamps(acquire_images_ret_val, expected_img_timestamps):
    for fut, est, expected_img_timestamp in zip_longest(*acquire_images_ret_val, expected_img_timestamps):
        img, img_timestamp = await fut
        assert abs(img_timestamp - expected_img_timestamp) < EPSILON_FOR_TIME


def _test_acquire_images_ret_val_est_timestamps(acquire_images_ret_val, expected_est_timestamps):
    for est, expected_est in zip_longest(acquire_images_ret_val[1], expected_est_timestamps):
        assert abs(est - expected_est) < EPSILON_FOR_TIME


# Test BaseImageSequenceImageAcquisitionImpl
@pytest.mark.parametrize('imgs', [
    [MOCK_IMAGE_0],
    [MOCK_IMAGE_0, MOCK_IMAGE_1, MOCK_IMAGE_2]
])
@pytest.mark.asyncio
async def test_base_image_seq_setting_images(imgs):
    baseimgs_impl = BaseImageSequenceImageAcquisitionImpl()
    baseimgs_impl._images = imgs

    baseimgs_impl.bn_frame_interval.set(1)

    await _test_acquire_images_ret_val_images(baseimgs_impl.acquire_images(), imgs)


@pytest.mark.parametrize('imgs', [
    [MOCK_IMAGE_0],
    [MOCK_IMAGE_0, MOCK_IMAGE_1, MOCK_IMAGE_2]
])
@pytest.mark.asyncio
async def test_base_image_seq_frame_interval(imgs):
    baseimgs_impl = BaseImageSequenceImageAcquisitionImpl()
    baseimgs_impl._images = imgs
    baseimgs_impl.bn_frame_interval.set(12.345)

    expected_img_timestamps = [i * 12.345 for i in range(len(imgs))]
    await _test_acquire_images_ret_val_timestamps(baseimgs_impl.acquire_images(), expected_img_timestamps)


@pytest.mark.parametrize('frame_interval', [
    None, 0, -1.2
])
def test_base_image_seq_acquire_images_with_invalid_frame_interval(frame_interval):
    baseimgs_impl = BaseImageSequenceImageAcquisitionImpl()
    baseimgs_impl._images = [MOCK_IMAGE_0, MOCK_IMAGE_1]
    baseimgs_impl.bn_frame_interval.set(frame_interval)

    # Frame interval must be > 0 and not None
    with pytest.raises(ValueError):
        baseimgs_impl.acquire_images()


@pytest.mark.parametrize('frame_interval', [
    None, 0, -1.2
])
def test_base_image_seq_acquire_images_with_invalid_frame_interval_but_only_one_image(frame_interval):
    baseimgs_impl = BaseImageSequenceImageAcquisitionImpl()
    baseimgs_impl._images = [MOCK_IMAGE_0]
    baseimgs_impl.bn_frame_interval.set(frame_interval)

    # Since only one image, should ignore frame_interval value.
    baseimgs_impl.acquire_images()


def test_base_image_seq_acquire_images_with_no_images():
    baseimgs_impl = BaseImageSequenceImageAcquisitionImpl()
    baseimgs_impl._images = []
    baseimgs_impl.bn_frame_interval.set(1)

    # _images can't be empty
    with pytest.raises(ValueError):
        baseimgs_impl.acquire_images()


@pytest.mark.parametrize('images, expected_image_size_hint', [
    (None, None),
    (tuple(), None),
    ((MOCK_IMAGE_0,), MOCK_IMAGE_0.shape[1::-1]),
    ((MOCK_IMAGE_0, MOCK_IMAGE_1, MOCK_IMAGE_2), MOCK_IMAGE_0.shape[1::-1]),
])
def test_base_image_seq_get_image_size_hint(images, expected_image_size_hint):
    baseimgs_impl = BaseImageSequenceImageAcquisitionImpl()
    baseimgs_impl._images = images
    image_size_hint = baseimgs_impl.get_image_size_hint()
    assert image_size_hint == expected_image_size_hint


@pytest.mark.parametrize('_images, expected_images', [
    (None, tuple()),
    ((MOCK_IMAGE_0,), (MOCK_IMAGE_0,)),
    ([MOCK_IMAGE_0, MOCK_IMAGE_1], (MOCK_IMAGE_0, MOCK_IMAGE_1)),

])
def test_base_image_seq_images_prop(_images, expected_images):
    baseimgs_impl = BaseImageSequenceImageAcquisitionImpl()
    baseimgs_impl._images = _images

    assert baseimgs_impl.images == expected_images


def test_base_image_seq_preview_is_initially_alive():
    images = (MOCK_IMAGE_0, MOCK_IMAGE_1, MOCK_IMAGE_2)

    baseimgs_impl = BaseImageSequenceImageAcquisitionImpl()
    baseimgs_impl._images = images

    preview = baseimgs_impl.create_preview()
    assert preview.bn_alive.get() is True


def test_base_image_seq_preview_config_num_images():
    images = (MOCK_IMAGE_0, MOCK_IMAGE_1, MOCK_IMAGE_2)

    baseimgs_impl = BaseImageSequenceImageAcquisitionImpl()
    baseimgs_impl._images = images

    preview = baseimgs_impl.create_preview()
    assert preview.config.bn_num_images.get() == len(images)


def test_base_image_seq_preview_config_index():
    images = (MOCK_IMAGE_0, MOCK_IMAGE_1, MOCK_IMAGE_2)

    baseimgs_impl = BaseImageSequenceImageAcquisitionImpl()
    baseimgs_impl._images = images

    preview = baseimgs_impl.create_preview()

    for i, image in enumerate(images):
        preview.config.bn_index.set(i)
        assert (preview.bn_image.get() == image).all()


def test_base_image_seq_preview_config_index_set_outside_range():
    images = (MOCK_IMAGE_0, MOCK_IMAGE_1, MOCK_IMAGE_2)

    baseimgs_impl = BaseImageSequenceImageAcquisitionImpl()
    baseimgs_impl._images = images

    preview = baseimgs_impl.create_preview()

    with pytest.raises(ValueError):
        preview.config.bn_index.set(3)


def test_base_image_seq_create_preview_when_no_images():
    baseimgs_impl = BaseImageSequenceImageAcquisitionImpl()
    baseimgs_impl._images = None

    with pytest.raises(ValueError):
        baseimgs_impl.create_preview()


def test_base_image_seq_create_preview_when_images_is_empty_sequence():
    baseimgs_impl = BaseImageSequenceImageAcquisitionImpl()
    baseimgs_impl._images = []

    with pytest.raises(ValueError):
        baseimgs_impl.create_preview()


def test_base_image_seq_preview_destroy():
    images = (MOCK_IMAGE_0, MOCK_IMAGE_1, MOCK_IMAGE_2)
    baseimgs_impl = BaseImageSequenceImageAcquisitionImpl()
    baseimgs_impl._images = images
    preview = baseimgs_impl.create_preview()

    # Destroy the preview
    preview.destroy()

    # Nothing really needs to happen, we just need to make sure the method exists.


# Test LocalImagesImageAcquisitionImpl

@pytest.mark.parametrize('img_paths', [
    [SAMPLE_IMAGES_DIR/'image0.png'],
    [SAMPLE_IMAGES_DIR/'image2.png',
     SAMPLE_IMAGES_DIR/'image0.png',
     SAMPLE_IMAGES_DIR/'image1.png']
])
def test_local_images_load_image_paths(img_paths):
    expected_imgs = [cv2.imread(str(img_path)) for img_path in sorted(img_paths)]
    expected_imgs = [cv2.cvtColor(img, cv2.COLOR_BGR2RGB) for img in expected_imgs]

    local_images = LocalImagesImageAcquisitionImpl()
    local_images.load_image_paths(img_paths)

    for actual_img, expected_img in zip_longest(local_images._images, expected_imgs):
        assert (actual_img == expected_img).all()


def test_local_images_load_nonexistent_image_path():
    local_images = LocalImagesImageAcquisitionImpl()
    with pytest.raises(ValueError):
        local_images.load_image_paths([SAMPLE_IMAGES_DIR/'this_image_does_not_exist.png'])


def test_local_images_last_loaded_paths():
    paths_to_load = (SAMPLE_IMAGES_DIR/'image0.png', SAMPLE_IMAGES_DIR/'image1.png')
    local_images = LocalImagesImageAcquisitionImpl()

    # Assert last loaded paths is initially an empty sequence
    assert tuple(local_images.bn_last_loaded_paths.get()) == ()

    # Load some images.
    local_images.load_image_paths(paths_to_load)

    # Assert last loaded paths is correct.
    assert tuple(local_images.bn_last_loaded_paths.get()) == paths_to_load

    # Use a sequence of strings for the path to load.
    local_images.load_image_paths(tuple(map(str, paths_to_load)))

    # Last loaded paths should still be a sequence of Path objects.
    assert tuple(local_images.bn_last_loaded_paths.get()) == paths_to_load


# Test BaseCameraImageAcquisitionImpl

@pytest.mark.asyncio
async def test_base_camera_acquire_images_images():
    class MyCamera(Camera):
        def __init__(self):
            self._images = [MOCK_IMAGE_0, MOCK_IMAGE_1, MOCK_IMAGE_2]

        def capture(self):
            return self._images.pop(0)

    base_camera = BaseCameraImageAcquisitionImpl()
    base_camera._camera = MyCamera()
    base_camera.bn_num_frames.set(2)
    base_camera.bn_frame_interval.set(0.01)

    await _test_acquire_images_ret_val_images(base_camera.acquire_images(), [MOCK_IMAGE_0, MOCK_IMAGE_1])


@pytest.mark.asyncio
async def test_base_camera_acquire_images_timestamps():
    base_camera = BaseCameraImageAcquisitionImpl()
    base_camera._camera = Mock()
    base_camera.bn_num_frames.set(2)
    base_camera.bn_frame_interval.set(1)

    now = time.time()
    expected_img_timestamps = [now, now + base_camera.bn_frame_interval.get()]

    acquire_images_ret_val = base_camera.acquire_images()
    await _test_acquire_images_ret_val_timestamps(acquire_images_ret_val, expected_img_timestamps)
    _test_acquire_images_ret_val_est_timestamps(acquire_images_ret_val, expected_img_timestamps)


@pytest.mark.parametrize('frame_interval', [
    None, 0, -1.2
])
def test_base_camera_acquire_images_with_invalid_frame_interval(frame_interval):
    base_camera = BaseCameraImageAcquisitionImpl()
    base_camera._camera = Mock()
    base_camera.bn_num_frames.set(2)
    base_camera.bn_frame_interval.set(frame_interval)

    # Frame interval must be > 0 and not None
    with pytest.raises(ValueError):
        base_camera.acquire_images()


@pytest.mark.parametrize('frame_interval', [
    None, 0, -1.2
])
def test_base_camera_acquire_images_with_invalid_frame_interval_but_only_one_image(frame_interval):
    base_camera = BaseCameraImageAcquisitionImpl()
    base_camera._camera = Mock()
    base_camera.bn_num_frames.set(1)
    base_camera.bn_frame_interval.set(frame_interval)

    # Since capturing only one image, should ignore frame_interval value.
    base_camera.acquire_images()


@pytest.mark.parametrize('num_frames', [
    None, -1, 0
])
def test_base_camera_acquire_images_with_invalid_num_frames(num_frames):
    base_camera = BaseCameraImageAcquisitionImpl()
    base_camera._camera = Mock()
    # Set a valid frame_interval
    base_camera.bn_frame_interval.set(1)

    # Set an invalid num_frames
    base_camera.bn_num_frames.set(num_frames)

    # num_frames must be > 0 and not None
    with pytest.raises(ValueError):
        base_camera.acquire_images()


@pytest.mark.asyncio
async def test_base_camera_acquire_images_cancel_futures():
    mock_camera = Mock()
    base_camera = BaseCameraImageAcquisitionImpl()
    base_camera._camera = mock_camera
    base_camera.bn_num_frames.set(3)
    base_camera.bn_frame_interval.set(0.01)
    futs, _ = base_camera.acquire_images()

    for fut in futs:
        fut.cancel()

    await asyncio.sleep(0.5)

    mock_camera.capture.assert_not_called()


def test_base_camera_acquire_images_with_camera_none():
    base_camera = BaseCameraImageAcquisitionImpl()
    base_camera._camera = None
    base_camera.bn_num_frames.set(3)
    base_camera.bn_frame_interval.set(1)

    with pytest.raises(ValueError):
        base_camera.acquire_images()


@pytest.mark.asyncio
async def test_base_camera_acquire_images_with_camera_that_cannot_capture():
    mock_camera = Mock()
    mock_camera.capture.side_effect = CameraCaptureError
    base_camera = BaseCameraImageAcquisitionImpl()
    base_camera._camera = mock_camera
    base_camera.bn_num_frames.set(3)
    base_camera.bn_frame_interval.set(0.01)

    for fut in base_camera.acquire_images()[0]:
        with pytest.raises(CameraCaptureError):
            await fut


@pytest.mark.asyncio
async def test_base_camera_acquire_images_with_camera_that_can_somtimes_capture():
    mock_camera = Mock()
    base_camera = BaseCameraImageAcquisitionImpl()
    base_camera._camera = mock_camera
    base_camera.bn_num_frames.set(5)
    base_camera.bn_frame_interval.set(0.01)

    futs = base_camera.acquire_images()[0]

    for fut in futs[:1]:
        await fut

    # Simulate the camera failing
    mock_camera.capture.side_effect = CameraCaptureError

    for fut in futs[1:2]:
        with pytest.raises(CameraCaptureError):
            await fut

    # Simulate the camera working again
    mock_camera.capture.side_effect = None

    for fut in futs[2:]:
        await fut


@pytest.mark.asyncio
async def test_base_camera_acquire_images_remove_camera_while_futures_pending():
    mock_camera = Mock()
    base_camera = BaseCameraImageAcquisitionImpl()
    base_camera._camera = mock_camera
    base_camera.bn_num_frames.set(3)
    base_camera.bn_frame_interval.set(0.1)
    futs, _ = base_camera.acquire_images()

    base_camera._camera = None

    for fut in futs:
        with pytest.raises(asyncio.CancelledError):
            await fut


def test_base_camera_get_image_size_hint():
    mock_camera = Mock()
    mock_camera.get_image_size_hint.return_value = (123, 456)
    base_camera = BaseCameraImageAcquisitionImpl()
    base_camera._camera = mock_camera

    assert base_camera.get_image_size_hint() == (123, 456)


def test_base_camera_when_no_camera():
    base_camera = BaseCameraImageAcquisitionImpl()

    assert base_camera.get_image_size_hint() is None


def test_base_camera_create_preview():
    mock_camera = Mock()
    mock_camera.capture.return_value = MOCK_IMAGE_0
    base_camera = BaseCameraImageAcquisitionImpl()
    base_camera._camera = mock_camera

    preview = base_camera.create_preview()
    assert preview.bn_alive.get() is True

    assert (preview.bn_image.get() == MOCK_IMAGE_0).all()


def test_base_camera_create_preview_with_camera_none():
    base_camera = BaseCameraImageAcquisitionImpl()
    base_camera._camera = None

    with pytest.raises(ValueError):
        base_camera.create_preview()


def test_base_camera_create_preview_with_camera_that_cannot_capture():
    mock_camera = Mock()
    mock_camera.capture.side_effect = CameraCaptureError
    base_camera = BaseCameraImageAcquisitionImpl()
    base_camera._camera = mock_camera

    with pytest.raises(ValueError):
        base_camera.create_preview()


@pytest.mark.asyncio
async def test_base_camera_create_preview_image():
    MIN_FPS = 10

    mock_camera = Mock()
    base_camera = BaseCameraImageAcquisitionImpl()
    base_camera._camera = mock_camera
    preview = base_camera.create_preview()

    cb = Mock()
    preview.bn_image.on_changed.connect(cb, immediate=True)

    mock_camera.capture.reset_mock()

    await asyncio.sleep(0.5)

    # Preview image should be retrieved from the camera lazily.
    mock_camera.capture.assert_not_called()
    # Retrieve image, this should capture a new image from the camera.
    preview.bn_image.get()

    await asyncio.sleep(0.5)

    # Retrieve another image.
    preview.bn_image.get()

    assert cb.call_count > MIN_FPS
    assert mock_camera.capture.call_count == 2


@pytest.mark.asyncio
async def test_base_camera_preview_destroy():
    mock_camera = Mock()
    base_camera = BaseCameraImageAcquisitionImpl()
    base_camera._camera = mock_camera
    preview = base_camera.create_preview()

    cb = Mock()
    preview.bn_image.on_changed.connect(cb, immediate=True)

    preview.destroy()
    assert preview.bn_alive.get() is False

    cb.reset_mock()
    mock_camera.capture.reset_mock()

    await asyncio.sleep(0.5)

    # Retrieve an image after preview destroyed
    preview.bn_image.get()

    cb.assert_not_called()
    mock_camera.capture.assert_not_called()


def test_base_camera_preview_dies_after_camera_is_set_to_none():
    base_camera = BaseCameraImageAcquisitionImpl()
    base_camera._camera = Mock()
    preview = base_camera.create_preview()

    base_camera._camera = None
    assert preview.bn_alive.get() is False


@pytest.mark.asyncio
async def test_base_camera_preview_ignores_capture_error():
    mock_camera = Mock()
    mock_camera.capture.return_value = MOCK_IMAGE_0
    base_camera = BaseCameraImageAcquisitionImpl()
    base_camera._camera = mock_camera
    preview = base_camera.create_preview()

    # Simulate the camera continuously failing to capture.
    mock_camera.capture.return_value = MOCK_IMAGE_1
    mock_camera.capture.side_effect = CameraCaptureError

    cb = Mock()
    preview.bn_image.on_changed.connect(cb, immediate=True)

    await asyncio.sleep(0.2)

    # The preview image should be the last image successfully captured by the camera.
    assert (preview.bn_image.get() == MOCK_IMAGE_0).all()

    # Simulate the camera working again.
    mock_camera.capture.side_effect = None

    await asyncio.sleep(0.2)

    assert (preview.bn_image.get() == MOCK_IMAGE_1).all()


# Test validation

@pytest.mark.parametrize('expected_valid, images', [
    (False, None),
    (False, tuple()),
    (True, (Mock(),)),
    (True, (Mock(), Mock()))
])
def test_base_image_sequence_image_acquisition_impl_validator_checks_images(expected_valid, images):
    target = BaseImageSequenceImageAcquisitionImpl()

    # Set a valid frame interval
    target.bn_frame_interval.set(1)

    # Set images to test value
    target._images = images

    assert target.validator.check_is_valid() is expected_valid


@pytest.mark.parametrize('expected_valid, frame_interval', [
    (False, None),
    (False, -12.3),
    (False, 0),
    (True, 1)
])
def test_base_image_sequence_image_acquisition_impl_validator_checks_frame_interval(expected_valid, frame_interval):
    target = BaseImageSequenceImageAcquisitionImpl()

    # Set valid images of length > 1
    target._images = [Mock(), Mock()]

    # Set frame interval to test value
    target.bn_frame_interval.set(frame_interval)

    assert target.validator.check_is_valid() is expected_valid


@pytest.mark.parametrize('invalid_frame_interval', [
    None,
    -12.3,
    0
])
def test_base_image_sequence_image_acquisition_impl_validator_invalid_frame_interval_with_one_image \
                (invalid_frame_interval):
    target = BaseImageSequenceImageAcquisitionImpl()

    # Set one valid image
    target._images = [Mock()]

    # Set frame interval to test value
    target.bn_frame_interval.set(invalid_frame_interval)

    assert target.validator.check_is_valid() is True


@pytest.mark.parametrize('expected_valid, camera', [
    (False, None),
    (True, Mock())
])
def test_base_camera_image_acquisition_impl_validator_checks_camera(expected_valid, camera):
    target = BaseCameraImageAcquisitionImpl()

    # Set valid num_frames and frame_interval
    target.bn_num_frames.set(2)
    target.bn_frame_interval.set(1)

    # Set camera to test value
    target._camera = camera

    assert target.validator.check_is_valid() is expected_valid


@pytest.mark.parametrize('expected_valid, num_frames', [
    (False, None),
    (False, -1),
    (False, 0),
    (True, 1)
])
def test_base_camera_image_acquisition_impl_validator_checks_num_frames(expected_valid, num_frames):
    target = BaseCameraImageAcquisitionImpl()

    # Set valid camera and frame_interval
    target._camera = Mock()
    target.bn_frame_interval.set(1)

    # Set num frames to test value
    target.bn_num_frames.set(num_frames)

    assert target.validator.check_is_valid() is expected_valid


@pytest.mark.parametrize('expected_valid, frame_interval', [
    (False, None),
    (False, -1.23),
    (False, 0),
    (True, 1.23)
])
def test_base_camera_image_acquisition_impl_validator_checks_frame_interval(expected_valid, frame_interval):
    target = BaseCameraImageAcquisitionImpl()

    # Set valid camera
    target._camera = Mock()
    # Set num_frames > 1
    target.bn_num_frames.set(2)

    # Set frame interval to test value
    target.bn_frame_interval.set(frame_interval)

    assert target.validator.check_is_valid() is expected_valid


@pytest.mark.parametrize('invalid_frame_interval', [
    None,
    -1.23,
    0
])
def test_base_camera_image_acquisition_impl_validator_invalid_frame_interval_with_num_frames_equal_one \
                (invalid_frame_interval):
    target = BaseCameraImageAcquisitionImpl()

    # Set valid camera
    target._camera = Mock()
    # Set num_frames to 1
    target.bn_num_frames.set(1)

    # Frame interval value should be ignored since only one frame to be captured
    target.bn_frame_interval.set(invalid_frame_interval)

    assert target.validator.check_is_valid() is True
