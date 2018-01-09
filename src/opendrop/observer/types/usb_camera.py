from typing import MutableMapping

import cv2
import numpy as np

from opendrop.observer import types
from opendrop.observer.bases import ObserverProvider, ObserverType
from opendrop.observer.types.camera import ICamera, CameraObserver
from opendrop.utility.resources import ResourceToken


class USBCamera(ICamera):
    PRECAPTURE = 5  # type: int

    def __init__(self, camera_index: int):
        self.vc = cv2.VideoCapture(camera_index)
        self.wait_until_ready()

        # For some reason, on some cameras, the first few images captured will be dark, so consume those images
        # now so the camera will be fully ready after initialisation.
        for i in range(self.PRECAPTURE):
            self.vc.read()

    def wait_until_ready(self) -> None:
        success = False

        while not success:
            if not self.vc.isOpened():
                raise ValueError('Camera failed to open.')

            success = self.vc.read()[0]

    def capture(self) -> np.ndarray:
        if not self.vc.isOpened():
            raise ValueError('VideoCapture is closed')

        while True:
            success, image = self.vc.read()

            if success:
                return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    def teardown(self) -> None:
        self.vc.release()


class USBCameraObserverProvider(ObserverProvider):
    def __init__(self):
        self._resource_cache = {}  # type: MutableMapping[int, ResourceToken[USBCamera]]

    def _get_resource_token(self, camera_index: int) -> ResourceToken[USBCamera]:
        if camera_index not in self._resource_cache:
            self._resource_cache[camera_index] = ResourceToken(USBCamera, camera_index=camera_index)

        return self._resource_cache[camera_index]

    def provide(self, camera_index: int) -> CameraObserver:
        return CameraObserver(self._get_resource_token(camera_index))


types.USB_CAMERA = ObserverType('USB Camera', USBCameraObserverProvider())
