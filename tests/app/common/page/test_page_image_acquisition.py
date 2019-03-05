from unittest.mock import Mock

from opendrop.app.common.model.image_acquisition.image_acquisition import ImageAcquisition
from opendrop.app.common.content.image_acquisition import _ImageAcquisitionFormPresenter
from opendrop.utility.bindable import BoxBindable


def test_root_presenter_connects_new_image_acquisition_impl_to_child_view():
    image_acquisition = ImageAcquisition()
    mock_view = Mock()
    mock_create_presenter_for_impl_and_view = Mock()
    presenter = _ImageAcquisitionFormPresenter(image_acquisition, mock_create_presenter_for_impl_and_view, Mock(), mock_view)

    mock_child_view = Mock()
    mock_image_acquisition_impl_type = Mock()
    mock_image_acquisition_impl = Mock()

    mock_view.configure_for.return_value = mock_child_view
    mock_image_acquisition_impl_type.impl_factory.return_value = mock_image_acquisition_impl

    # Change the image acquisition type
    image_acquisition.type = mock_image_acquisition_impl_type

    # Assert that root presenter tells root view to show configuration view of new type
    mock_view.configure_for.assert_called_once_with(mock_image_acquisition_impl_type)
    # Assert that root presenter calls factory function to create new presenter to connect image acquisition impl and
    # new child configuration view.
    mock_create_presenter_for_impl_and_view.assert_called_once_with(mock_image_acquisition_impl, mock_child_view)


def test_root_presenter_connects_existing_image_acquisition_impl_to_child_view():
    image_acquisition = ImageAcquisition()
    mock_view = Mock()
    mock_create_presenter_for_impl_and_view = Mock()

    mock_child_view = Mock()
    mock_image_acquisition_impl_type = Mock()
    mock_image_acquisition_impl = Mock()

    mock_view.configure_for.return_value = mock_child_view
    mock_image_acquisition_impl_type.impl_factory.return_value = mock_image_acquisition_impl

    # Change the image acquisition type
    image_acquisition.type = mock_image_acquisition_impl_type

    # Then initialise the presenter
    presenter = _ImageAcquisitionFormPresenter(image_acquisition, mock_create_presenter_for_impl_and_view, Mock(), mock_view)

    # Assert that root presenter tells root view to show configuration view of the existing type
    mock_view.configure_for.assert_called_once_with(mock_image_acquisition_impl_type)
    # Assert that root presenter calls factory function to create new presenter to connect image acquisition impl and
    # new child configuration view.
    mock_create_presenter_for_impl_and_view.assert_called_once_with(mock_image_acquisition_impl, mock_child_view)


def test_root_presenter_initialised_with_image_acquisition_with_no_impl():
    image_acquisition = ImageAcquisition()
    mock_view = Mock()
    mock_create_presenter_for_impl_and_view = Mock()

    # Initialise the presenter
    presenter = _ImageAcquisitionFormPresenter(image_acquisition, mock_create_presenter_for_impl_and_view, Mock(), mock_view)

    # Assert that root presenter did not tell the view to show the configuration view for an implementation of `None`.
    mock_view.configure_for.assert_not_called()
    # Assert that root presenter did not call the factory function to create new presenter for an implementation of
    # `None`.
    mock_create_presenter_for_impl_and_view.assert_not_called()


def test_root_presenter_destroys_old_impl_presenter():
    image_acquisition = ImageAcquisition()
    mock_old_presenter = Mock()
    mock_create_presenter_for_impl_and_view = Mock(return_value=mock_old_presenter)

    presenter = _ImageAcquisitionFormPresenter(image_acquisition, mock_create_presenter_for_impl_and_view, Mock(), Mock())

    # Change the image acquisition type.
    image_acquisition.type = Mock()

    # Change the return value to something other than mock_old_presenter.
    mock_create_presenter_for_impl_and_view.return_value = None

    # Change the image acquisition type again.
    image_acquisition.type = Mock()

    # Assert the old presenter was destroyed.
    mock_old_presenter.destroy.assert_called_once_with()


def test_root_presenter_tells_view_of_available_types():
    mock_impl_types = (Mock(), Mock(), Mock())
    mock_view = Mock()
    presenter = _ImageAcquisitionFormPresenter(Mock(), Mock(), mock_impl_types, mock_view)

    mock_view.set_available_types.assert_called_once_with(mock_impl_types)


def test_root_presenter_syncs_view_user_input_impl_type():
    image_acquisition = ImageAcquisition()
    mock_view = Mock()
    mock_view.bn_user_input_impl_type = BoxBindable(None)

    mock_impl_type_0 = Mock()
    image_acquisition.type = mock_impl_type_0

    presenter = _ImageAcquisitionFormPresenter(image_acquisition, Mock(), Mock(), mock_view)

    # Assert that root presenter syncs image acquisition existing type.
    assert mock_view.bn_user_input_impl_type.get() is mock_impl_type_0

    mock_impl_type_1 = Mock()
    image_acquisition.type = mock_impl_type_1

    # Assert that root presenter updates view when image acquisition changes types.
    assert mock_view.bn_user_input_impl_type.get() is mock_impl_type_1

    # Simulate a user changing the impl. type.
    mock_impl_type_2 = Mock()
    mock_view.bn_user_input_impl_type.set(mock_impl_type_2)

    # Assert that when the user changes the impl. type, the root presenter will relay this change to image acquisition.
    assert image_acquisition.type is mock_impl_type_2


def test_root_presenter_destroy():
    image_acquisition = ImageAcquisition()
    mock_view = Mock()
    mock_view.bn_user_input_impl_type = BoxBindable(None)
    presenter = _ImageAcquisitionFormPresenter(image_acquisition, Mock(), Mock(), mock_view)

    # Destroy the presenter.
    presenter.destroy()

    # Change the image acquisition type after the presenter has been destroyed.
    mock_impl_type_0 = Mock()
    image_acquisition.type = mock_impl_type_0

    assert mock_view.bn_user_input_impl_type.get() is None
    mock_view.configure_for.assert_not_called()

    # Simulate a user changing the impl. type.
    mock_impl_type_1 = Mock()
    mock_view.bn_user_input_impl_type.set(mock_impl_type_1)

    assert image_acquisition.type is mock_impl_type_0


def test_root_presenter_destroy_with_impl_presenter():
    image_acquisition = ImageAcquisition()
    mock_old_presenter = Mock()
    mock_create_presenter_for_impl_and_view = Mock(return_value=mock_old_presenter)

    presenter = _ImageAcquisitionFormPresenter(image_acquisition, mock_create_presenter_for_impl_and_view, Mock(), Mock())

    # Change the image acquisition type.
    image_acquisition.type = Mock()

    # Destroy the presenter
    presenter.destroy()

    # Assert the impl. presenter was also destroyed.
    mock_old_presenter.destroy.assert_called_once_with()
