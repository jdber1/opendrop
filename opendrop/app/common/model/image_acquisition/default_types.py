import asyncio
import functools
import time
from abc import abstractmethod
from asyncio import Future
from pathlib import Path
from typing import Union, Sequence, MutableSequence, Tuple, Optional, TypeVar, Generic

import cv2
import numpy as np

from opendrop.mytypes import Image
from opendrop.utility.events import Event, EventConnection
from opendrop.utility.simplebindable import Bindable, BoxBindable, AccessorBindable, apply as bn_apply
from opendrop.utility.validation import validate, check_is_not_empty, check_is_positive
from .image_acquisition import ImageAcquisitionImplType, ImageAcquisitionImpl, ImageAcquisitionPreview, ScheduledImage

T = TypeVar('T')


# Local images.

class ImageSequenceImageAcquisitionPreviewConfig:
    def __init__(self, preview: 'ImageSequenceImageAcquisitionPreview') -> None:
        self.bn_index = preview._bn_index
        self.bn_num_images = preview._bn_num_images


class ImageSequenceImageAcquisitionPreview(ImageAcquisitionPreview[ImageSequenceImageAcquisitionPreviewConfig]):
    def __init__(self, images: Sequence[Image]) -> None:
        assert len(images) > 0
        self.on_image_changed = Event()

        self._index = 0
        self._images = images

        self._bn_index = AccessorBindable(self._get_index, self._set_index)
        self._bn_num_images = AccessorBindable(self._get_num_images)

        self.bn_alive = BoxBindable(True)
        self.config = ImageSequenceImageAcquisitionPreviewConfig(self)

    @property
    def image(self) -> Image:
        return self._images[self._index]

    def _get_index(self) -> int:
        return self._index

    def _set_index(self, new_index: int) -> None:
        if new_index not in range(self._get_num_images()):
            raise ValueError('index out of range, got index {} (number of images = {})'
                             .format(new_index, self._get_num_images()))

        self._index = new_index
        self.on_image_changed.fire(self.Transition.JUMP)

    def _get_num_images(self) -> int:
        return len(self._images)


class BaseImageSequenceImageAcquisitionImpl(ImageAcquisitionImpl):
    class _ScheduledImageImpl(ScheduledImage):
        def __init__(self, image: Image, timestamp: float) -> None:
            self._image = image
            self._timestamp = timestamp

        async def read(self) -> Tuple[Image, float]:
            return self._image, self._timestamp

    def __init__(self) -> None:
        self._loop = asyncio.get_event_loop()
        self._bn_images = BoxBindable(tuple())  # type: Bindable[Sequence[Image]]

        self.bn_frame_interval = BoxBindable(None)  # type: Bindable[Optional[int]]

        # Input validation

        frame_interval_err_enabled = bn_apply(
            lambda images: len(images) != 1 if images is not None else True,
            self._bn_images)
        self.frame_interval_err = validate(
            value=self.bn_frame_interval,
            checks=(check_is_not_empty, check_is_positive),
            enabled=frame_interval_err_enabled)

    @property
    def _images(self) -> Sequence[Image]:
        return self._bn_images.get()

    @_images.setter
    def _images(self, new_images: Sequence[Image]) -> None:
        self._bn_images.set(new_images)

    def acquire_images(self) -> Tuple[Sequence[Future], Sequence[float]]:
        images = self._images
        frame_interval = self.bn_frame_interval.get()

        if len(images) == 0:
            raise ValueError("_images can't be empty")

        if frame_interval is None or frame_interval <= 0:
            if len(images) == 1:
                # Since only one image, we don't care about the frame_interval.
                frame_interval = 0
            else:
                raise ValueError('Frame interval must be > 0 and not None, currently: `{}`'.format(frame_interval))

        result = []

        for i, img in enumerate(self._images):
            result.append(self._ScheduledImageImpl(img, i * frame_interval))

        return result

    def create_preview(self) -> ImageAcquisitionPreview[ImageSequenceImageAcquisitionPreviewConfig]:
        if self._images is None:
            raise ValueError('Failed to create preview, _images cannot be None')
        elif len(self._images) == 0:
            raise ValueError('Failed to create preview, _images is empty')

        return ImageSequenceImageAcquisitionPreview(list(self._images))

    def get_image_size_hint(self) -> Optional[Tuple[int, int]]:
        if self._images is None or len(self._images) == 0:
            return

        first_image = self._images[0]
        return first_image.shape[1::-1]

    @property
    def images(self) -> Sequence[Image]:
        return tuple(self._images) if self._images is not None else tuple()

    @property
    def has_errors(self) -> bool:
        if len(self.images) == 0:
            # Images can't be empty
            return True

        return bool(self.frame_interval_err.get())


class LocalImagesImageAcquisitionImpl(BaseImageSequenceImageAcquisitionImpl):
    def __init__(self) -> None:
        super().__init__()
        self._last_loaded_paths = tuple()  # type: Sequence[Path]
        self.bn_last_loaded_paths = AccessorBindable(self._get_last_loaded_paths)

    def _get_last_loaded_paths(self) -> Sequence[Path]:
        return self._last_loaded_paths

    def load_image_paths(self, img_paths: Sequence[Union[Path, str]]) -> None:
        img_paths = sorted([p for p in map(Path, img_paths) if not p.is_dir()])

        imgs = []  # type: MutableSequence[np.ndarray]
        for img_path in img_paths:
            img = cv2.imread(str(img_path))
            if img is None:
                raise ValueError("Failed to load image from path '{}'".format(img_path))

            # OpenCV loads image in BGR mode, but the rest of our app works with images in the RGB colourspace, so
            # convert the loaded image appropriately.
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            imgs.append(img)

        self._images = imgs
        self._last_loaded_paths = tuple(map(Path, img_paths))
        self.bn_last_loaded_paths.poke()


# USB camera

class CameraCaptureError(Exception):
    """Raised when a camera capture fails."""


class Camera:
    @abstractmethod
    def capture(self) -> np.ndarray:
        """Return the captured image."""

    @abstractmethod
    def get_image_size_hint(self) -> Optional[Tuple[int, int]]:
        """Implementation of get_image_size_hint()"""


class CameraImageAcquisitionPreview(ImageAcquisitionPreview):
    POKE_IDLE_INTERVAL = 0.20

    def __init__(self, src_impl: 'BaseCameraImageAcquisitionImpl', first_image: Image) -> None:
        self._loop = asyncio.get_event_loop()
        self._src_impl = src_impl

        self.on_image_changed = Event()

        self._buffer = first_image
        self._buffer_outdated = False
        self._poke_image_loop_timer_handle = None  # type: Optional[asyncio.TimerHandle]

        self.bn_alive = BoxBindable(True)

        self.__event_connections = [
            self._src_impl._on_camera_changed.connect(self.destroy)
        ]

        self._poke_image_loop()

    def destroy(self) -> None:
        if not self.bn_alive.get():
            return

        if self._poke_image_loop_timer_handle is not None:
            self._poke_image_loop_timer_handle.cancel()

        for ec in self.__event_connections:
            ec.disconnect()

        self.bn_alive.set(False)

    def _poke_image_loop(self) -> None:
        if self.bn_alive.get() is False:
            return

        self._buffer_outdated = True
        self.on_image_changed.fire(self.Transition.SMOOTH)

        self._poke_image_loop_timer_handle = self._loop.call_later(self.POKE_IDLE_INTERVAL, self._poke_image_loop)

    @property
    def image(self) -> Image:
        if self.bn_alive.get() and self._buffer_outdated:
            self._update_buffer()

        return self._buffer

    def _update_buffer(self) -> None:
        try:
            self._buffer = self._src_impl._camera.capture()
        except CameraCaptureError:
            pass

        self._buffer_outdated = False


CameraType = TypeVar('CameraType', bound=Camera)


class BaseCameraImageAcquisitionImpl(Generic[CameraType], ImageAcquisitionImpl):
    class _ScheduledImageImpl(ScheduledImage):
        def __init__(self, image_and_timestamp_fut: Future, est_ready: float) -> None:
            self._image_and_timestamp_fut = image_and_timestamp_fut
            self.est_ready = est_ready

        async def read(self) -> Tuple[Image, float]:
            return await self._image_and_timestamp_fut

        def cancel(self) -> None:
            self._image_and_timestamp_fut.cancel()

    def __init__(self) -> None:
        self._loop = asyncio.get_event_loop()

        self._actual_camera = None  # type: Optional[CameraType]
        self._on_camera_changed = Event()
        self.bn_num_frames = BoxBindable(1)
        self.bn_frame_interval = BoxBindable(None)  # type: Bindable[Optional[float]]

        # Input validation
        self.num_frames_err = validate(self.bn_num_frames, checks=(check_is_not_empty, check_is_positive))

        frame_interval_err_enabled = bn_apply(lambda n: n != 1, self.bn_num_frames)
        self.frame_interval_err = validate(
            self.bn_frame_interval,
            checks=(check_is_not_empty, check_is_positive),
            enabled=frame_interval_err_enabled)

    @property
    def _camera(self) -> Optional[CameraType]:
        return self._actual_camera

    @_camera.setter
    def _camera(self, new_camera: CameraType) -> None:
        self._actual_camera = new_camera
        self._on_camera_changed.fire()

    def acquire_images(self) -> Sequence[ScheduledImage]:
        if self._camera is None:
            raise ValueError("_camera can't be None")

        num_frames = self.bn_num_frames.get()

        if num_frames is None or num_frames <= 0:
            raise ValueError('num_frames must be > 0 and not None, currently: {}'.format(num_frames))

        frame_interval = self.bn_frame_interval.get()

        if frame_interval is None or frame_interval <= 0:
            if num_frames == 1:
                frame_interval = 0
            else:
                raise ValueError('Frame interval must be > 0 and not None, currently: `{}`')

        acquire_start_loop_time = self._loop.time()
        acquire_start_unix_time = time.time()

        results = []

        for i in range(num_frames):
            fut = Future()
            capture_at_rel_time = i * frame_interval
            capture_at_loop_time = acquire_start_loop_time + capture_at_rel_time
            capture_at_unix_time = acquire_start_unix_time + capture_at_rel_time

            handle = self._loop.call_at(capture_at_loop_time, self._capture_and_set_future, fut)
            fut.add_done_callback(functools.partial(self._cancel_handle_if_fut_cancelled, handle=handle))

            results.append(self._ScheduledImageImpl(fut, capture_at_unix_time))

        return results

    def create_preview(self) -> ImageAcquisitionPreview[None]:
        if self._camera is None:
            raise ValueError('Cannot create preview when _camera is None')

        try:
            first_image = self._camera.capture()
        except CameraCaptureError as exc:
            raise ValueError('Failed to create preview, camera failed to capture.') from exc

        return CameraImageAcquisitionPreview(self, first_image)

    def get_image_size_hint(self) -> Optional[Tuple[int, int]]:
        camera = self._camera
        if camera is None:
            return

        return camera.get_image_size_hint()

    @staticmethod
    def _cancel_handle_if_fut_cancelled(fut: Future, handle: asyncio.TimerHandle) -> None:
        if fut.cancelled():
            handle.cancel()

    def _capture_and_set_future(self, fut: Future) -> None:
        if fut.cancelled():
            return

        if self._camera is None:
            fut.cancel()
            return

        try:
            fut.set_result((self._camera.capture(), time.time()))
        except CameraCaptureError:
            fut.cancel()

    @property
    def has_errors(self) -> bool:
        if self._camera is None:
            return True

        return bool(self.frame_interval_err.get()) or bool(self.num_frames_err.get())


class USBCamera(Camera):
    _PRECAPTURE = 5
    _CAPTURE_TIMEOUT = 0.5

    def __init__(self, cam_idx: int) -> None:
        self._vc = cv2.VideoCapture(cam_idx)

        if not self.check_vc_works(timeout=5):
            raise ValueError('Camera failed to open.')

        self.bn_alive = BoxBindable(True)

        # For some reason, on some cameras, the first few images captured will be dark. Consume those images
        # now so the camera will be "fully operational" after initialisation.
        for i in range(self._PRECAPTURE):
            self._vc.read()

    @property
    def alive(self) -> bool:
        return self.bn_alive.get()

    @alive.setter
    def alive(self, value: bool) -> None:
        self.bn_alive.set(value)

    def capture(self) -> np.ndarray:
        start_time = time.time()
        while self._vc.isOpened() and (time.time() - start_time) < self._CAPTURE_TIMEOUT:
            success, image = self._vc.read()

            if success:
                return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        self.release()
        raise CameraCaptureError

    def get_image_size_hint(self) -> Optional[Tuple[int, int]]:
        width = self._vc.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = self._vc.get(cv2.CAP_PROP_FRAME_HEIGHT)
        return width, height

    def check_vc_works(self, timeout: float) -> bool:
        start_time = time.time()
        while self._vc.isOpened() and (time.time() - start_time) < timeout:
            success = self._vc.grab()
            if success:
                # Camera still works
                return True
        else:
            return False

    def release_if_not_working(self, timeout=_CAPTURE_TIMEOUT) -> None:
        if not self.check_vc_works(timeout):
            self.release()

    def release(self) -> None:
        self._vc.release()
        self.alive = False


class USBCameraImageAcquisitionImpl(BaseCameraImageAcquisitionImpl[USBCamera]):
    def __init__(self):
        super().__init__()
        self._current_camera_index = None  # type: Optional[int]
        self.bn_current_camera_index = AccessorBindable(self._get_current_camera_index)
        self._camera_alive_changed_event_connection = None  # type: Optional[EventConnection]

        # Input validation
        self.current_camera_index_err = validate(self.bn_current_camera_index, checks=(check_is_not_empty,))

    def open_camera(self, cam_idx: int) -> None:
        try:
            new_camera = USBCamera(cam_idx)
        except ValueError:
            raise ValueError('Failed to open camera with camera index = {}'.format(cam_idx))

        self.remove_current_camera(_poke_current_camera_index=False)

        self._camera = new_camera
        self._camera_alive_changed_event_connection = new_camera.bn_alive.on_changed \
            .connect(self._hdl_camera_alive_changed)
        self._current_camera_index = cam_idx
        self.bn_current_camera_index.poke()

    def remove_current_camera(self, _poke_current_camera_index: bool = True) -> None:
        """Release and remove the current camera, if it exists. Specify `_poke_current_camera_index=False` to avoid
        poking self.bn_current_camera_index."""
        camera = self._camera

        if camera is None:
            return

        if camera.alive:
            camera.release()

        assert self._camera_alive_changed_event_connection is not None
        assert self._camera_alive_changed_event_connection.status is EventConnection.Status.CONNECTED
        self._camera_alive_changed_event_connection.disconnect()

        self._camera = None
        self._camera_alive_changed_event_connection = None
        self._current_camera_index = None

        if _poke_current_camera_index:
            self.bn_current_camera_index.poke()

    def check_camera_still_working(self) -> None:
        if self._camera is None:
            # There is no camera to check
            return

        self._camera.release_if_not_working()

    def _get_current_camera_index(self) -> int:
        return self._current_camera_index

    def _hdl_camera_alive_changed(self) -> None:
        camera = self._camera
        assert camera is not None

        if camera.alive is False:
            self.remove_current_camera()

    @property
    def has_errors(self) -> bool:
        if super().has_errors:
            return True
        return bool(self.current_camera_index_err.get())

    def destroy(self) -> None:
        if self._camera is not None:
            self._camera.release()
            self._camera = None

        super().destroy()


class DefaultImageAcquisitionImplType(ImageAcquisitionImplType):
    LOCAL_IMAGES = ('Local images', LocalImagesImageAcquisitionImpl)
    USB_CAMERA = ('USB camera', USBCameraImageAcquisitionImpl)
