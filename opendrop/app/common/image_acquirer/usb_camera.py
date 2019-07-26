import time
from typing import Tuple, Optional

import cv2
import numpy as np

from opendrop.utility.bindable import BoxBindable, AccessorBindable
from opendrop.utility.events import EventConnection
from .camera import CameraAcquirer, Camera, CameraCaptureError


class USBCameraAcquirer(CameraAcquirer):
    def __init__(self):
        super().__init__()

        self._camera_index = None  # type: Optional[int]
        self.bn_camera_index = AccessorBindable(getter=self._get_camera_index)

        self._camera_alive_changed_ec = None  # type: Optional[EventConnection]

    def open_camera(self, camera_index: int) -> None:
        try:
            new_camera = USBCamera(camera_index)
        except ValueError:
            raise ValueError(
                "Failed to open camera with camera index: '{}'"
                .format(camera_index)
            )

        self.remove_current_camera(_poke_current_camera_index=False)

        self.bn_camera.set(new_camera)
        self._camera_alive_changed_ec = \
            new_camera.bn_alive.on_changed.connect(self._hdl_camera_alive_changed)

        self._camera_index = camera_index
        self.bn_camera_index.poke()

    def remove_current_camera(self, _poke_current_camera_index: bool = True) -> None:
        """Release and remove the current camera, if it exists. Specify `_poke_current_camera_index=False` to avoid
        poking self.bn_current_camera_index.
        """
        camera = self.bn_camera.get()
        if camera is None:
            return

        assert self._camera_alive_changed_ec is not None
        assert self._camera_alive_changed_ec.status is EventConnection.Status.CONNECTED

        self._camera_alive_changed_ec.disconnect()
        self._camera_alive_changed_ec = None

        if camera.bn_alive.get():
            camera.release()

        self.bn_camera.set(None)
        self._camera_index = None

        if _poke_current_camera_index:
            self.bn_camera_index.poke()

    def check_camera_still_working(self) -> None:
        camera = self.bn_camera.get()

        if camera is None:
            # There is no camera to check
            return

        camera.release_if_not_working()

    def _get_camera_index(self) -> int:
        return self._camera_index

    def _hdl_camera_alive_changed(self) -> None:
        camera = self.bn_camera.get()
        assert camera is not None

        if camera.bn_alive.get() is False:
            self.remove_current_camera()

    def destroy(self) -> None:
        self.remove_current_camera(_poke_current_camera_index=False)
        super().destroy()


class USBCamera(Camera):
    _PRECAPTURE = 5
    _CAPTURE_TIMEOUT = 0.5

    def __init__(self, camera_index: int) -> None:
        self._vc = cv2.VideoCapture(camera_index)

        self.bn_alive = BoxBindable(True)

        if not self.check_vc_works(timeout=5):
            raise ValueError('Camera failed to open.')

        # For some reason, on some cameras, the first few images captured will be dark. Consume those images now so the
        # camera will be "fully operational" after initialisation.
        for i in range(self._PRECAPTURE):
            self._vc.read()

    def check_vc_works(self, timeout: float) -> bool:
        start_time = time.time()
        while self._vc.isOpened() and (time.time() - start_time) < timeout:
            success = self._vc.grab()
            if success:
                # Camera still works
                return True
        else:
            return False

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

    def release_if_not_working(self, timeout=_CAPTURE_TIMEOUT) -> None:
        if not self.check_vc_works(timeout):
            self.release()

    def release(self) -> None:
        self._vc.release()
        self.bn_alive.set(False)
