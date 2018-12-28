from opendrop.app.common.analysis_model.image_acquisition.default_types import BaseImageSequenceImageAcquisitionImpl, \
    BaseCameraImageAcquisitionImpl
from opendrop.app.common.validation.image_acquisition.validator import ImageAcquisitionImplValidator


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
