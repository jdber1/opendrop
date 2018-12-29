from typing import Callable, Optional

from opendrop.app.common.analysis_model.image_acquisition.image_acquisition import ImageAcquisition, \
    ImageAcquisitionImpl
from opendrop.utility.bindable.bindable import BaseAtomicBindable, AtomicBindableAdapter


class ImageAcquisitionImplValidator:
    is_valid = False  # type: bool

    def destroy(self) -> None:
        """Destroy this object, perform any necessary cleanup tasks."""


class ImageAcquisitionValidator:
    def __init__(self, create_subvalidator_for_impl: Callable[[ImageAcquisitionImpl], ImageAcquisitionImplValidator],
                 target: ImageAcquisition) -> None:
        self._target = target
        self._subvalidator = None  # type: Optional[ImageAcquisitionImplValidator]
        self._create_subvalidator_for_impl = create_subvalidator_for_impl

        self.bn_subvalidator = AtomicBindableAdapter(self._get_subvalidator)  # type: AtomicBindableAdapter[ImageAcquisitionImplValidator]

        self._target.bn_impl.on_changed.connect(self._hdl_target_impl_changed, immediate=True)
        self._hdl_target_impl_changed()

    @property
    def is_valid(self) -> bool:
        if self._target.impl is None:
            # Image acquisition has no chosen implementation, this is not valid.
            return False

        subvalidator = self._subvalidator
        assert subvalidator is not None

        return subvalidator.is_valid

    def _get_subvalidator(self) -> ImageAcquisitionImplValidator:
        return self._subvalidator

    def _hdl_target_impl_changed(self) -> None:
        old_subvalidator = self._subvalidator

        if old_subvalidator is not None:
            old_subvalidator.destroy()

        new_subvalidator = None

        new_impl = self._target.bn_impl.get()
        if new_impl is not None:
            new_subvalidator = self._create_subvalidator_for_impl(new_impl)

        self._subvalidator = new_subvalidator
        self.bn_subvalidator.poke()
