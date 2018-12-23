from unittest.mock import Mock

import pytest

from opendrop.app.common.analysis_model.image_acquisition.image_acquisition import ImageAcquisition, \
    ImageAcquisitionImplType, ImageAcquisitionImpl


class MockImAcqImpl(ImageAcquisitionImpl):
    LOG_ACQUIRE_IMAGES = 'LOG_ACQUIRE_IMAGES'
    LOG_CREATE_PREVIEW = 'LOG_CREATE_PREVIEW'
    LOG_GET_MODEL_ERRORS = 'LOG_GET_MODEL_ERRORS'

    acquire_images_return_val = (list(range(5)), list(range(5)))
    create_preview_return_val = object()
    get_model_errors_return_val = object()

    def __init__(self):
        # Used for testing.
        self.log = []

    def acquire_images(self):
        self.log.append(self.LOG_ACQUIRE_IMAGES)
        return self.acquire_images_return_val

    def create_preview(self):
        self.log.append(self.LOG_CREATE_PREVIEW)
        return self.create_preview_return_val

    def get_model_errors(self):
        self.log.append(self.LOG_GET_MODEL_ERRORS)
        return self.get_model_errors_return_val


def mock0_impl_factory():
    impl = MockImAcqImpl()
    MyImAcqImplType.MOCK0.created_impls.append(impl)
    return impl


class MyImAcqImplType(ImageAcquisitionImplType):
    MOCK0 = (mock0_impl_factory,)

    def __init__(self, *args, **kwargs):
        ImageAcquisitionImplType.__init__(self, *args, **kwargs)

        # Used for testing.
        self.created_impls = []


def test_im_acq_initial_impl():
    im_acq = ImageAcquisition()

    assert im_acq.type is None
    assert im_acq.bn_type.get() is None
    assert im_acq.impl is None
    assert im_acq.bn_impl.get() is None


@pytest.mark.parametrize('mode', [0, 1])
def test_im_acq_change_type(mode):
    im_acq = ImageAcquisition()
    hdl_im_acq_bn_type_changed = Mock()
    im_acq.bn_type.on_changed.connect(hdl_im_acq_bn_type_changed, immediate=True)
    hdl_im_acq_bn_impl_changed = Mock()
    im_acq.bn_impl.on_changed.connect(hdl_im_acq_bn_impl_changed, immediate=True)

    # Change type (using two ways)
    if mode == 0:
        im_acq.type = MyImAcqImplType.MOCK0
    else:
        im_acq.bn_type.set(MyImAcqImplType.MOCK0)

    hdl_im_acq_bn_type_changed.assert_called_once_with()
    assert im_acq.type is MyImAcqImplType.MOCK0
    assert im_acq.bn_type.get() is MyImAcqImplType.MOCK0

    hdl_im_acq_bn_impl_changed.assert_called_once_with()
    assert im_acq.impl in MyImAcqImplType.MOCK0.created_impls
    assert im_acq.bn_impl.get() in MyImAcqImplType.MOCK0.created_impls


def test_im_acq_acquire_images():
    im_acq = ImageAcquisition()
    im_acq.type = MyImAcqImplType.MOCK0

    # Clear the log.
    im_acq.impl.log = []

    # Acquire images.
    res = im_acq.acquire_images()

    assert im_acq.impl.log == [MockImAcqImpl.LOG_ACQUIRE_IMAGES]
    assert res == MockImAcqImpl.acquire_images_return_val


def test_im_acq_acquire_images_when_impl_is_none():
    im_acq = ImageAcquisition()

    with pytest.raises(ValueError):
        im_acq.acquire_images()


def test_im_acq_create_preview():
    im_acq = ImageAcquisition()
    im_acq.type = MyImAcqImplType.MOCK0

    # Clear the log.
    im_acq.impl.log = []

    # Acquire images.
    res = im_acq.create_preview()

    assert im_acq.impl.log == [MockImAcqImpl.LOG_CREATE_PREVIEW]
    assert res == MockImAcqImpl.create_preview_return_val


def test_im_acq_create_preview_when_impl_is_none():
    im_acq = ImageAcquisition()

    with pytest.raises(ValueError):
        im_acq.create_preview()


def test_im_acq_get_model_errors():
    im_acq = ImageAcquisition()
    im_acq.type = MyImAcqImplType.MOCK0

    # Clear the log.
    im_acq.impl.log = []

    # Acquire images.
    res = im_acq.get_model_errors()

    assert im_acq.impl.log == [MockImAcqImpl.LOG_GET_MODEL_ERRORS]
    assert res == MockImAcqImpl.get_model_errors_return_val


def test_im_acq_get_model_errors_when_impl_is_none():
    im_acq = ImageAcquisition()

    with pytest.raises(ValueError):
        im_acq.get_model_errors()
