from asyncio import Future
from enum import Enum
from typing import Generic, TypeVar, Type, Callable, Optional, Tuple, List, Any, Sequence

from opendrop.mytypes import Image
from opendrop.utility.bindable.bindable import AtomicBindable, AtomicBindableAdapter, AtomicBindablePropertyAdapter


class ImageAcquisitionImplType(Enum):
    def __init__(self, impl_factory: Callable[[], 'ImageAcquisitionImpl']) -> None:
        self.impl_factory = impl_factory


class ImageAcquisitionImpl:
    def acquire_images(self) -> Tuple[List[Future], List[float]]:
        """Implementation of acquire_images()"""

    def create_preview(self) -> Tuple[AtomicBindable[Image], Any]:
        """Return a tuple, first element is an AtomicBindable that provides the current preview image and the second
        element is a configuration object that is used to configure the first element."""


T = TypeVar('T', bound=ImageAcquisitionImplType)


class ImageAcquisition(Generic[T]):
    def __init__(self, types: Type[T]) -> None:
        self._impl = None  # type: Optional[ImageAcquisitionImpl]
        self.bn_impl = AtomicBindableAdapter(self._get_impl)  # type: AtomicBindable[Optional[ImageAcquisitionImpl]]

    def acquire_images(self) -> Tuple[List[Future], List[float]]:
        """Return a tuple, with the first element being a list of futures which will be resolved to each image, and the
        second element being a list of estimated timestamps for when the futures will be resolved."""
        if self.impl is None:
            raise ValueError('No implementation chosen yet')

        futs, tims = self.impl.acquire_images()

        # Check that the number of futures matches the number of estimated timestamps.
        assert len(futs) == len(tims)

        return futs, tims

    def create_preview(self) -> Tuple[AtomicBindable[Image], Any]:
        if self.impl is None:
            raise ValueError('No implementation chosen yet')

        return self.impl.create_preview()

    def get_model_errors(self) -> Sequence:
        if self.impl is None:
            raise ValueError('No implementation chosen yet')

        return self.impl.get_model_errors()

    def change_type(self, new_type: T) -> None:
        self._set_impl(new_type.impl_factory())

    @AtomicBindablePropertyAdapter
    def impl(self) -> AtomicBindable[Optional[ImageAcquisitionImpl]]:
        return self.bn_impl

    def _get_impl(self) -> Optional[ImageAcquisitionImpl]:
        return self._impl

    def _set_impl(self, new_impl: Optional[ImageAcquisitionImpl]) -> None:
        self._impl = new_impl
        self.bn_impl.poke()
