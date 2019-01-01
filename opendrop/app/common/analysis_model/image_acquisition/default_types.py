import asyncio
import functools
import time
from abc import abstractmethod
from asyncio import Future
from pathlib import Path
from typing import Union, Sequence, MutableSequence, Tuple, Optional, Any, TypeVar, Generic

import cv2
import numpy as np

from opendrop.app.common.analysis_model.image_acquisition.image_acquisition import ImageAcquisitionImplType, \
    ImageAcquisitionImpl, ImageAcquisitionPreview
from opendrop.mytypes import Image
from opendrop.utility.bindable.bindable import AtomicBindableVar, AtomicBindableAdapter, BaseAtomicBindable, \
    Bindable, AtomicBindable, AtomicBindableTx
from opendrop.utility.events import Event, EventConnection

T = TypeVar('T')


# Local images.

class ImageSequenceImageAcquisitionPreviewConfig:
    def __init__(self, preview: 'ImageSequenceImageAcquisitionPreview') -> None:
        self.bn_index = preview._bn_index
        self.bn_num_images = preview._bn_num_images


class ImageSequenceImageAcquisitionPreview(ImageAcquisitionPreview[ImageSequenceImageAcquisitionPreviewConfig]):
    def __init__(self, images: Sequence[Image]) -> None:
        assert len(images) > 0

        self._index = 0
        self._images = images

        self._bn_index = AtomicBindableAdapter(self._get_index, self._set_index)  # type: AtomicBindableAdapter[int]
        self._bn_num_images = AtomicBindableAdapter(self._get_num_images)  # type: AtomicBindableAdapter[int]

        self.bn_image = AtomicBindableAdapter(self._get_image)  # type: AtomicBindableAdapter[Image]
        self.bn_alive = AtomicBindableVar(True)  # type: AtomicBindable[bool]
        self.config = ImageSequenceImageAcquisitionPreviewConfig(self)

    def _get_image(self) -> Image:
        return self._images[self._index]

    def _get_index(self) -> int:
        return self._index

    def _set_index(self, new_index: int) -> None:
        if new_index not in range(self._get_num_images()):
            raise ValueError('index out of range, got index {} (number of images = {})'
                             .format(new_index, self._get_num_images()))

        self._index = new_index
        self.bn_image.poke()

    def _get_num_images(self) -> int:
        return len(self._images)


class BaseImageSequenceImageAcquisitionImpl(ImageAcquisitionImpl):
    def __init__(self) -> None:
        self._loop = asyncio.get_event_loop()
        self._images = []  # type: MutableSequence[np.ndarray]

        self.bn_frame_interval = AtomicBindableVar(None)  # type: AtomicBindable[int]

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

        futs = []
        ests = []

        for i, img in enumerate(self._images):
            fut = self._loop.create_future()
            fut.set_result((img, i * frame_interval))
            futs.append(fut)
            ests.append(time.time())

        return futs, ests

    def create_preview(self) -> ImageAcquisitionPreview[ImageSequenceImageAcquisitionPreviewConfig]:
        if self._images is None:
            raise ValueError('Failed to create preview, _images cannot be None')
        elif len(self._images) == 0:
            raise ValueError('Failed to create preview, _images is empty')

        return ImageSequenceImageAcquisitionPreview(list(self._images))

    @property
    def images(self) -> Sequence[Image]:
        return tuple(self._images) if self._images is not None else tuple()


class LocalImagesImageAcquisitionImpl(BaseImageSequenceImageAcquisitionImpl):
    def __init__(self) -> None:
        super().__init__()
        self._last_loaded_paths = tuple()  # type: Sequence[Path]
        self.bn_last_loaded_paths = AtomicBindableAdapter(self._get_last_loaded_paths)  # type: AtomicBindableVar[Sequence[Path]]

    def _get_last_loaded_paths(self) -> Sequence[Path]:
        return self._last_loaded_paths

    def load_image_paths(self, img_paths: Sequence[Union[Path, str]]) -> None:
        imgs = []  # type: MutableSequence[np.ndarray]
        for img_path in img_paths:
            img = cv2.imread(str(img_path))
            if img is None:
                raise ValueError("Failed to load image from path '{}'".format(img_path))
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


class CameraImageAcquisitionPreview(ImageAcquisitionPreview):
    POKE_IDLE_INTERVAL = 0.05

    # These two classes are kind of a bodge, ImageBindable is compatible to being used as a read-only
    # BaseAtomicBindable[Image].
    class ImageBindableTx(AtomicBindableTx[Image]):
        def __init__(self, src_bn: 'CameraImageAcquisitionPreview.ImageBindable') -> None:
            self._src_bn = src_bn

        @property
        def value(self) -> Image:
            return self._src_bn.get()

    class ImageBindable(AtomicBindable[Image]):
        def __init__(self, preview: 'CameraImageAcquisitionPreview') -> None:
            super().__init__()
            self._preview = preview

        def get(self) -> Image:
            return self._preview._get_image()

        def set(self, value: Any) -> None:
            raise AttributeError('Cannot set image attribute')

        def poke(self) -> None:
            self.on_changed.fire()
            self._bcast_tx(self._create_tx())

        def _create_tx(self) -> 'CameraImageAcquisitionPreview.ImageBindableTx':
            return CameraImageAcquisitionPreview.ImageBindableTx(self)

        def _export(self) -> 'CameraImageAcquisitionPreview.ImageBindableTx':
            return self._create_tx()

        def _raw_apply_tx(self, tx: 'CameraImageAcquisitionPreview.ImageBindableTx') \
                -> Optional[Sequence['CameraImageAcquisitionPreview.ImageBindableTx']]:
            raise NotImplementedError

    def __init__(self, src_impl: 'BaseCameraImageAcquisitionImpl', first_image: Image) -> None:
        self._loop = asyncio.get_event_loop()

        self._src_impl = src_impl
        self._buffer = first_image
        self._buffer_outdated = False
        self._alive = True
        self._poke_image_loop_timer_handle = None  # type: Optional[asyncio.TimerHandle]

        self.bn_alive = AtomicBindableAdapter(self._get_alive)  # type: AtomicBindableAdapter[bool]
        self.bn_image = self.ImageBindable(self)  # type: CameraImageAcquisitionPreview.ImageBindable[Image]

        self.__event_connections = [
            self._src_impl._on_camera_changed.connect(self._hdl_src_impl_camera_changed, immediate=True)
        ]

        self._poke_image_loop()

    def destroy(self) -> None:
        self._alive = False

        if self._poke_image_loop_timer_handle is not None:
            self._poke_image_loop_timer_handle.cancel()

        for ec in self.__event_connections:
            ec.disconnect()

        self.bn_alive.poke()

    def _hdl_src_impl_camera_changed(self) -> None:
        self.destroy()

    def _get_alive(self) -> bool:
        return self._alive

    def _poke_image_loop(self) -> None:
        if self._alive is False:
            return

        self._buffer_outdated = True
        self.bn_image.poke()

        self._poke_image_loop_timer_handle = self._loop.call_later(self.POKE_IDLE_INTERVAL, self._poke_image_loop)

    def _get_image(self) -> Image:
        if self._alive and self._buffer_outdated:
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
    def __init__(self) -> None:
        self._loop = asyncio.get_event_loop()

        self._actual_camera = None  # type: Optional[CameraType]
        self._on_camera_changed = Event()
        self.bn_num_frames = AtomicBindableVar(1)  # type: AtomicBindable[int]
        self.bn_frame_interval = AtomicBindableVar(None)  # type: AtomicBindable[float]

    @property
    def _camera(self) -> Optional[CameraType]:
        return self._actual_camera

    @_camera.setter
    def _camera(self, new_camera: CameraType) -> None:
        self._actual_camera = new_camera
        self._on_camera_changed.fire()

    def acquire_images(self) -> Tuple[Sequence[Future], Sequence[float]]:
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

        futs = []
        ests = []

        for i in range(num_frames):
            fut = Future()
            capture_at_rel_time = i * frame_interval
            capture_at_loop_time = acquire_start_loop_time + capture_at_rel_time
            capture_at_unix_time = acquire_start_unix_time + capture_at_rel_time

            handle = self._loop.call_at(capture_at_loop_time, self._capture_and_set_future, fut)
            futs.append(fut)
            fut.add_done_callback(functools.partial(self._cancel_handle_if_fut_cancelled, handle=handle))
            ests.append(capture_at_unix_time)

        return futs, ests

    def create_preview(self) -> ImageAcquisitionPreview[None]:
        if self._camera is None:
            raise ValueError('Cannot create preview when _camera is None')

        try:
            first_image = self._camera.capture()
        except CameraCaptureError as exc:
            raise ValueError('Failed to create preview, camera failed to capture.') from exc

        return CameraImageAcquisitionPreview(self, first_image)

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
        except CameraCaptureError as exc:
            fut.set_exception(exc)


class USBCamera(Camera):
    _PRECAPTURE = 5
    _CAPTURE_TIMEOUT = 0.5

    def __init__(self, cam_idx: int) -> None:
        self._vc = cv2.VideoCapture(cam_idx)
        self.wait_until_ready()

        # For some reason, on some cameras, the first few images captured will be dark. Consume those images
        # now so the camera will be "fully operational" after initialisation.
        for i in range(self._PRECAPTURE):
            self._vc.read()

        self.bn_alive = AtomicBindableVar(True)

    # Property adapters for atomic bindables
    alive = AtomicBindable.property_adapter(lambda self: self.bn_alive)

    def wait_until_ready(self) -> None:
        success = False

        while not success:
            if not self._vc.isOpened():
                raise ValueError('Camera failed to open.')

            success = self._vc.read()[0]

    def capture(self) -> np.ndarray:
        start_time = time.time()
        while self._vc.isOpened() and (time.time() - start_time) < self._CAPTURE_TIMEOUT:
            success, image = self._vc.read()

            if success:
                return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        self.release()
        raise CameraCaptureError

    def check_still_working(self) -> None:
        start_time = time.time()
        while self._vc.isOpened() and (time.time() - start_time) < self._CAPTURE_TIMEOUT:
            success = self._vc.grab()
            if success:
                # Camera still works
                return

        self.release()

    def release(self) -> None:
        self._vc.release()
        self.alive = False


class USBCameraImageAcquisitionImpl(BaseCameraImageAcquisitionImpl[USBCamera]):
    def __init__(self):
        super().__init__()
        self._current_camera_index = None  # type: Optional[int]
        self.bn_current_camera_index = AtomicBindableAdapter(self._get_current_camera_index)  # type: AtomicBindableAdapter[Optional[int]]
        self._camera_alive_changed_event_connection = None  # type: Optional[EventConnection]

    def open_camera(self, cam_idx: int) -> None:
        try:
            new_camera = USBCamera(cam_idx)
        except ValueError:
            raise ValueError('Failed to open camera with camera index = {}'.format(cam_idx))

        self.remove_current_camera(_poke_current_camera_index=False)

        self._camera = new_camera
        self._camera_alive_changed_event_connection = new_camera.bn_alive.on_changed \
            .connect(self._hdl_camera_alive_changed, immediate=True)
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

        self._camera.check_still_working()

    def _get_current_camera_index(self) -> int:
        return self._current_camera_index

    def _hdl_camera_alive_changed(self) -> None:
        camera = self._camera
        assert camera is not None

        if camera.alive is False:
            self.remove_current_camera()

    def destroy(self) -> None:
        if self._camera is not None:
            self._camera.release()
            self._camera = None

        super().destroy()


class DefaultImageAcquisitionImplType(ImageAcquisitionImplType):
    LOCAL_IMAGES = ('Local images', LocalImagesImageAcquisitionImpl)
    USB_CAMERA = ('USB camera', USBCameraImageAcquisitionImpl)
