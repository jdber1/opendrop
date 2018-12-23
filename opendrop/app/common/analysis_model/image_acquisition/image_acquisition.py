from asyncio import Future
from enum import Enum
from typing import Generic, TypeVar, Callable, Optional, Tuple, Any, Sequence

from opendrop.mytypes import Image
from opendrop.utility.bindable.bindable import AtomicBindable, AtomicBindableAdapter, AtomicBindablePropertyAdapter


class ImageAcquisitionImplType(Enum):
    def __init__(self, impl_factory: Callable[[], 'ImageAcquisitionImpl']) -> None:
        self.impl_factory = impl_factory


class ImageAcquisitionImpl:
    def acquire_images(self) -> Tuple[Sequence[Future], Sequence[float]]:
        """Implementation of acquire_images()"""

    def create_preview(self) -> Tuple[AtomicBindable[Image], Any]:
        """Implementation of create_preview()"""


T = TypeVar('T', bound=ImageAcquisitionImplType)


class ImageAcquisition(Generic[T]):
    def __init__(self) -> None:
        self._type = None  # type: Optional[T]
        self._impl = None  # type: Optional[ImageAcquisitionImpl]
        self.bn_impl = AtomicBindableAdapter(self._get_impl)  # type: AtomicBindable[Optional[ImageAcquisitionImpl]]
        self.bn_type = AtomicBindableAdapter(self._get_type, self._set_type)  # type: AtomicBindable[Optional[T]]

    def acquire_images(self) -> Tuple[Sequence[Future], Sequence[float]]:
        """Return a tuple, with the first element being a sequence of futures which will be resolved to a tuple of an
        image and the image's timestamp, and the second element being a sequence of estimated unix timestamps for when
        the futures will be resolved."""
        if self.impl is None:
            raise ValueError('No implementation chosen yet')

        futs, tims = self.impl.acquire_images()

        # Check that the number of futures matches the number of estimated timestamps.
        assert len(futs) == len(tims)

        return futs, tims

    def create_preview(self) -> Tuple[AtomicBindable[Image], Any]:
        """Return a tuple, first element is an AtomicBindable that provides the current preview image and the second
        element is a configuration object that is used to configure the first element."""
        if self.impl is None:
            raise ValueError('No implementation chosen yet')

        return self.impl.create_preview()

    def get_model_errors(self) -> Sequence:
        if self.impl is None:
            raise ValueError('No implementation chosen yet')

        return self.impl.get_model_errors()

    @AtomicBindablePropertyAdapter
    def type(self) -> AtomicBindable[Optional[T]]:
        return self.bn_type

    def _get_type(self) -> Optional[T]:
        return self._type

    def _set_type(self, new_type: T) -> None:
        self._set_impl(new_type.impl_factory())
        self._type = new_type

    @AtomicBindablePropertyAdapter
    def impl(self) -> AtomicBindable[Optional[ImageAcquisitionImpl]]:
        return self.bn_impl

    def _get_impl(self) -> Optional[ImageAcquisitionImpl]:
        return self._impl

    def _set_impl(self, new_impl: Optional[ImageAcquisitionImpl]) -> None:
        self._impl = new_impl
        self.bn_impl.poke()
