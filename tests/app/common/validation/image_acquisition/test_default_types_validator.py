from unittest.mock import Mock

import pytest

from opendrop.app.common.analysis_model.image_acquisition.default_types import BaseImageSequenceImageAcquisitionImpl, \
    BaseCameraImageAcquisitionImpl
from opendrop.app.common.validation.image_acquisition.default_types_validator import \
    BaseImageSequenceImageAcquisitionImplValidator, BaseCameraImageAcquisitionImplValidator


@pytest.mark.parametrize('images, expected_valid', [
    (None, False),
    (tuple(), False),
    ((Mock(),), True),
    ((Mock(), Mock()), True)
])
def test_base_image_sequence_image_acquisition_impl_validator_checks_images(images, expected_valid):
    target = BaseImageSequenceImageAcquisitionImpl()
    subvalidator = BaseImageSequenceImageAcquisitionImplValidator(target)
    # Set a valid frame interval
    target.bn_frame_interval.set(1)

    target._images = images
    assert subvalidator.is_valid is expected_valid


@pytest.mark.parametrize('frame_interval, expected_valid', [
    (None, False),
    (-12.3, False),
    (0, False),
    (1, True)
])
def test_base_image_sequence_image_acquisition_impl_validator_checks_frame_interval(frame_interval, expected_valid):
    target = BaseImageSequenceImageAcquisitionImpl()
    subvalidator = BaseImageSequenceImageAcquisitionImplValidator(target)

    # Set valid images
    target._images = [Mock()]

    target.bn_frame_interval.set(frame_interval)
    assert subvalidator.is_valid is expected_valid


@pytest.mark.parametrize('camera, expected_valid', [
    (None, False),
    (Mock(), True)
])
def test_base_camera_image_acquisition_impl_validator_checks_camera(camera, expected_valid):
    target = BaseCameraImageAcquisitionImpl()
    subvalidator = BaseCameraImageAcquisitionImplValidator(target)

    # Set valid num_frames and frame_interval
    target.bn_num_frames.set(1)
    target.bn_frame_interval.set(1)

    target._camera = camera
    assert subvalidator.is_valid is expected_valid


@pytest.mark.parametrize('num_frames, expected_valid', [
    (None, False),
    (-1, False),
    (0, False),
    (1, True)
])
def test_base_camera_image_acquisition_impl_validator_checks_camera(num_frames, expected_valid):
    target = BaseCameraImageAcquisitionImpl()
    subvalidator = BaseCameraImageAcquisitionImplValidator(target)

    # Set valid camera and frame_interval
    target._camera = Mock()
    target.bn_frame_interval.set(1)

    target.bn_num_frames.set(num_frames)
    assert subvalidator.is_valid is expected_valid


@pytest.mark.parametrize('frame_interval, expected_valid', [
    (None, False),
    (-1.23, False),
    (0, False),
    (1.23, True)
])
def test_base_camera_image_acquisition_impl_validator_checks_camera(frame_interval, expected_valid):
    target = BaseCameraImageAcquisitionImpl()
    subvalidator = BaseCameraImageAcquisitionImplValidator(target)

    # Set valid camera and num_frames
    target._camera = Mock()
    target.bn_num_frames.set(1)

    target.bn_frame_interval.set(frame_interval)
    assert subvalidator.is_valid is expected_valid
