from unittest.mock import Mock, PropertyMock

from opendrop.app.common.analysis_model.image_acquisition.image_acquisition import ImageAcquisition
from opendrop.app.common.validation.image_acquisition.validator import ImageAcquisitionValidator


def test_image_acquisition_validator_creates_subvalidator_for_new_impl():
    img_acq = ImageAcquisition()

    mock_im_acq_type = Mock()
    mock_im_acq_impl = Mock()
    mock_im_acq_type.impl_factory.return_value = mock_im_acq_impl

    mock_subvalidator = Mock()
    mock_create_subvalidator_for_impl = Mock(return_value=mock_subvalidator)

    validator = ImageAcquisitionValidator(mock_create_subvalidator_for_impl, img_acq)

    # Change image acquisition implementation type
    img_acq.type = mock_im_acq_type

    # Assert that the "subvalidator" factory was called
    mock_create_subvalidator_for_impl.assert_called_with(mock_im_acq_impl)
    # Assert that the subvalidator being used was the one created by the factory.
    assert validator.bn_subvalidator.get() == mock_subvalidator


def test_image_acquisition_validator_creates_subvalidator_for_existing_impl():
    img_acq = ImageAcquisition()

    mock_im_acq_type = Mock()
    mock_im_acq_impl = Mock()
    mock_im_acq_type.impl_factory.return_value = mock_im_acq_impl

    mock_subvalidator = Mock()
    mock_create_subvalidator_for_impl = Mock(return_value=mock_subvalidator)

    # Change image acquisition implementation type
    img_acq.type = mock_im_acq_type

    # Instantiate the validator with an ImageAcquisition that already has a chosen implementation.
    validator = ImageAcquisitionValidator(mock_create_subvalidator_for_impl, img_acq)

    # Assert that the "subvalidator" factory was called
    mock_create_subvalidator_for_impl.assert_called_with(mock_im_acq_impl)
    # Assert that the subvalidator being used was the one created by the factory.
    assert validator.bn_subvalidator.get() == mock_subvalidator


def test_image_acquisition_validator_destroys_old_subvalidator():
    img_acq = ImageAcquisition()
    validator = ImageAcquisitionValidator(Mock(), img_acq)

    # Change image acquisition implementation type
    img_acq.type = Mock()

    old_subvalidator = validator.bn_subvalidator.get()

    # Change image acquisition implementation type again
    img_acq.type = Mock()

    old_subvalidator.destroy.assert_called_once_with()


def test_image_acquisition_validator_is_valid_delegates_to_subvalidator():
    expected_is_valid_value = Mock()
    is_valid_prop_mock = PropertyMock(return_value=expected_is_valid_value)

    class MockSubvalidator:
        is_valid = is_valid_prop_mock

    img_acq = ImageAcquisition()
    validator = ImageAcquisitionValidator(Mock(return_value=MockSubvalidator()), img_acq)
    img_acq.type = Mock()

    actual_is_valid_value = validator.is_valid

    is_valid_prop_mock.assert_called_once_with()
    assert actual_is_valid_value == expected_is_valid_value


def test_image_acquisition_validator_is_valid_when_im_acq_has_no_impl():
    img_acq = ImageAcquisition()
    validator = ImageAcquisitionValidator(Mock(), img_acq)

    assert validator.is_valid is False
