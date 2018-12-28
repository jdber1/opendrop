from typing import TypeVar, Callable, Type, MutableMapping

from opendrop.app.common.analysis_model.image_acquisition.default_types import BaseImageSequenceImageAcquisitionImpl, \
    BaseCameraImageAcquisitionImpl, LocalImagesImageAcquisitionImpl, USBCameraImageAcquisitionImpl
from opendrop.app.common.analysis_model.image_acquisition.image_acquisition import ImageAcquisitionImpl
from opendrop.app.common.validation.image_acquisition.validator import ImageAcquisitionImplValidator

# New types

ValidatorFactory = Callable[[ImageAcquisitionImpl], ImageAcquisitionImplValidator]

# Dependency injection stuff

impl_to_subvalidator_factory = {}  # type: MutableMapping[Type[ImageAcquisitionImpl], ValidatorFactory]


T = TypeVar('T', bound=ValidatorFactory)
def this_can_validate(impl: Type[ImageAcquisitionImpl]) -> Callable[[T], T]:
    def actual(validator_factory: T) -> T:
        impl_to_subvalidator_factory[impl] = validator_factory
        return validator_factory
    return actual


def create_subvalidator_for_impl(impl: ImageAcquisitionImpl) -> ImageAcquisitionImplValidator:
    return impl_to_subvalidator_factory[type(impl)](impl)


# Main classes start here

@this_can_validate(LocalImagesImageAcquisitionImpl)
class BaseImageSequenceImageAcquisitionImplValidator(ImageAcquisitionImplValidator):
    def __init__(self, target: BaseImageSequenceImageAcquisitionImpl) -> None:
        self._target = target

    @property
    def is_valid(self) -> bool:
        target = self._target

        if len(target.images) == 0:
            return False

        if target.bn_frame_interval.get() <= 0:
            return False

        return True


@this_can_validate(USBCameraImageAcquisitionImpl)
class BaseCameraImageAcquisitionImplValidator(ImageAcquisitionImplValidator):
    def __init__(self, target: BaseCameraImageAcquisitionImpl) -> None:
        self._target = target

    @property
    def is_valid(self) -> bool:
        target = self._target

        if target._camera is None:
            return False

        if target.bn_num_frames.get() <= 0:
            return False

        if target.bn_frame_interval.get() <= 0:
            return False

        return True
