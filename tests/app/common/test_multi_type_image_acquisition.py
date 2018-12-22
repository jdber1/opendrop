from unittest.mock import Mock

import pytest

from opendrop.app.common.analysis_model.multi_type_image_acquisition import MultiTypeImageAcquisition, \
    MultiTypeImageAcquisitionImplType, MultiTypeImageAcquisitionImpl


class MockMTIAImpl(MultiTypeImageAcquisitionImpl):
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
    impl = MockMTIAImpl()
    MyMTIAImplType.MOCK0.created_impls.append(impl)
    return impl


class MyMTIAImplType(MultiTypeImageAcquisitionImplType):
    MOCK0 = (mock0_impl_factory,)

    def __init__(self, *args, **kwargs):
        MultiTypeImageAcquisitionImplType.__init__(self, *args, **kwargs)

        # Used for testing.
        self.created_impls = []


def test_mtia_initial_impl():
    mtia = MultiTypeImageAcquisition(MyMTIAImplType)

    assert mtia.impl is None
    assert mtia.bn_impl.get() is None


def test_mtia_change_type():
    mtia = MultiTypeImageAcquisition(MyMTIAImplType)
    cb = Mock()
    mtia.bn_impl.on_changed.connect(cb, immediate=True)

    # Change type
    mtia.change_type(MyMTIAImplType.MOCK0)

    cb.assert_called_once_with()
    assert mtia.impl in MyMTIAImplType.MOCK0.created_impls
    assert mtia.bn_impl.get() in MyMTIAImplType.MOCK0.created_impls


def test_mtia_acquire_images():
    mtia = MultiTypeImageAcquisition(MyMTIAImplType)
    mtia.change_type(MyMTIAImplType.MOCK0)

    # Clear the log.
    mtia.impl.log = []

    # Acquire images.
    res = mtia.acquire_images()

    assert mtia.impl.log == [MockMTIAImpl.LOG_ACQUIRE_IMAGES]
    assert res == MockMTIAImpl.acquire_images_return_val


def test_mtia_acquire_images_when_impl_is_none():
    mtia = MultiTypeImageAcquisition(MyMTIAImplType)

    with pytest.raises(ValueError):
        mtia.acquire_images()


def test_mtia_create_preview():
    mtia = MultiTypeImageAcquisition(MyMTIAImplType)
    mtia.change_type(MyMTIAImplType.MOCK0)

    # Clear the log.
    mtia.impl.log = []

    # Acquire images.
    res = mtia.create_preview()

    assert mtia.impl.log == [MockMTIAImpl.LOG_CREATE_PREVIEW]
    assert res == MockMTIAImpl.create_preview_return_val


def test_mtia_create_preview_when_impl_is_none():
    mtia = MultiTypeImageAcquisition(MyMTIAImplType)

    with pytest.raises(ValueError):
        mtia.create_preview()


def test_mtia_get_model_errors():
    mtia = MultiTypeImageAcquisition(MyMTIAImplType)
    mtia.change_type(MyMTIAImplType.MOCK0)

    # Clear the log.
    mtia.impl.log = []

    # Acquire images.
    res = mtia.get_model_errors()

    assert mtia.impl.log == [MockMTIAImpl.LOG_GET_MODEL_ERRORS]
    assert res == MockMTIAImpl.get_model_errors_return_val


def test_mtia_get_model_errors_when_impl_is_none():
    mtia = MultiTypeImageAcquisition(MyMTIAImplType)

    with pytest.raises(ValueError):
        mtia.get_model_errors()
