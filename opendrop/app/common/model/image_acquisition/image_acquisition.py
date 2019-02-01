import math
from abc import abstractmethod, ABC
from enum import Enum
from typing import Generic, TypeVar, Callable, Optional, Tuple, Sequence

from opendrop.mytypes import Image
from opendrop.utility.bindable.bindable import AtomicBindableAdapter, AtomicBindable
from opendrop.utility.events import Event


class ScheduledImage(ABC):
    est_ready = math.nan

    @abstractmethod
    async def read(self) -> Tuple[Image, float]:
        """Return the image and timestamp."""

    def cancel(self) -> None:
        pass


class ImageAcquisitionImplType(Enum):
    def __init__(self, display_name: str, impl_factory: Callable[[], 'ImageAcquisitionImpl']) -> None:
        self.display_name = display_name
        self.impl_factory = impl_factory


class ImageAcquisitionImpl:
    def acquire_images(self) -> Sequence[ScheduledImage]:
        """Implementation of acquire_images()"""

    def create_preview(self) -> 'ImageAcquisitionPreview':
        """Implementation of create_preview()"""

    def get_image_size_hint(self) -> Optional[Tuple[int, int]]:
        """Implementation of get_image_size_hint()"""

    @property
    def has_errors(self) -> bool:
        """Whether or not errors exist in the configuration of this implementation."""

    def destroy(self) -> None:
        """Destroy this object, perform any necessary cleanup tasks."""


ConfigType = TypeVar('ConfigType')


class ImageAcquisitionPreview(Generic[ConfigType]):
    class Transition(Enum):
        JUMP = 0
        SMOOTH = 1

    bn_alive = None  # type: AtomicBindable[bool]

    image = None  # type: Image
    config = None  # type: ConfigType

    on_image_changed = None  # type: Event

    def destroy(self) -> None:
        """Perform clean up any routines and destroy this preview, cannot be undone."""


ImplType = TypeVar('ImplType', bound=ImageAcquisitionImplType)


class ImageAcquisition(Generic[ImplType]):
    def __init__(self) -> None:
        self._type = None  # type: Optional[ImplType]
        self._impl = None  # type: Optional[ImageAcquisitionImpl]
        self.bn_impl = AtomicBindableAdapter(self._get_impl)  # type: AtomicBindableAdapter[Optional[ImageAcquisitionImpl]]
        self.bn_type = AtomicBindableAdapter(self._get_type, self._set_type)  # type: AtomicBindableAdapter[Optional[ImplType]]

    # Property adapters for atomic bindables.
    type = AtomicBindable.property_adapter(lambda self: self.bn_type)
    impl = AtomicBindable.property_adapter(lambda self: self.bn_impl)

    def acquire_images(self) -> Sequence[ScheduledImage]:
        """Return a tuple, with the first element being a sequence of futures which will be resolved to a tuple of an
        image and the image's timestamp, and the second element being a sequence of estimated unix timestamps for when
        the futures will be resolved."""
        if self.impl is None:
            raise ValueError('No implementation chosen yet')

        return self.impl.acquire_images()

    def create_preview(self) -> ImageAcquisitionPreview:
        if self.impl is None:
            raise ValueError('No implementation chosen yet')

        return self.impl.create_preview()

    def get_image_size_hint(self) -> Optional[Tuple[int, int]]:
        """Return the best guess of what size the acquired images will have. If a sensible size cannot be determined,
        return None."""
        if self.impl is None:
            raise ValueError('No implementation chosen yet')

        return self.impl.get_image_size_hint()

    def _get_type(self) -> Optional[ImplType]:
        return self._type

    def _set_type(self, new_type: ImplType) -> None:
        self._set_impl(new_type.impl_factory())
        self._type = new_type

    def _get_impl(self) -> Optional[ImageAcquisitionImpl]:
        return self._impl

    def _set_impl(self, new_impl: Optional[ImageAcquisitionImpl]) -> None:
        old_impl = self._impl
        if old_impl is not None:
            old_impl.destroy()

        self._impl = new_impl
        self.bn_impl.poke()

    @property
    def has_errors(self) -> bool:
        if self._impl is None:
            # Image acquisition has no chosen implementation, this is not valid.
            return True

        return self._impl.has_errors

    def destroy(self) -> None:
        if self._impl is not None:
            self._impl.destroy()
