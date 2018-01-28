from abc import abstractmethod
import asyncio
from asyncio import Task
from typing import List, Optional, Sequence

import numpy as np
import time

from opendrop.observer.bases import Observer, Observation, ObserverPreview
from opendrop.utility.resources import IResource, ResourceToken


class ICamera(IResource):
    @abstractmethod
    def capture(self) -> np.ndarray: pass


class CameraObserver(Observer):
    def __init__(self, cam_token: ResourceToken[ICamera]) -> None:
        self.cam_token = cam_token

    # `Observation`s returned are in ascending order of timestamp
    def timelapse(self, timestamps: Sequence[float]) -> List[Observation]:
        event_loop = asyncio.get_event_loop()  # type: asyncio.AbstractEventLoop
        now = event_loop.time()  # type: float

        # Acquire the camera resource, release it later when the observations are captured.
        cam = self.cam_token.acquire()  # type: ICamera

        observations = []  # type: List[Observation]

        for t in timestamps:
            new_observation = Observation()  # type: Observation
            event_loop.call_at(now + t, lambda o: o.load(cam.capture()), new_observation)

            observations.append(new_observation)

        # Once the last observation is done, release the camera.
        observations[-1].events.on_ready.connect(cam.release, once=True, ignore_args=True, strong_ref=True)

        return observations

    def preview(self) -> 'CameraObserverPreview':
        return CameraObserverPreview(self)

    def acquire_camera(self) -> ICamera:
        return self.cam_token.acquire()


# NEEDS EVENT LOOP TO BE RUNNING!!!
class CameraObserverPreview(ObserverPreview):
    def __init__(self, observer: CameraObserver) -> None:
        super().__init__(observer)

        self.alive = True  # type: bool

        self._cam = observer.acquire_camera()  # type: ICamera
        self._frame_interval = 0  # type: float
        self._step_task = None  # type: Optional[Task]
        self._last_update = 0  # type: float

        self._schedule_step()

    async def _step(self) -> None:
        if self._frame_interval == -1:
            return

        now = asyncio.get_event_loop().time()
        delta = now - self._last_update

        if delta < self._frame_interval:
            await asyncio.sleep(self._frame_interval - delta)
        else:
            self.events.on_update.fire(self._cam.capture())
            self._last_update = now

        self._schedule_step()

    def _schedule_step(self) -> None:
        if self.alive:
            self._step_task = asyncio.get_event_loop().create_task(self._step())

    def _cancel_step(self) -> None:
        if self._step_task is not None:
            self._step_task.cancel()

    def _reset_step(self) -> None:
        if self._step_task and not self._step_task.done():
            self._cancel_step()

        self._schedule_step()

    def close(self) -> None:
        if not self.alive:
            raise ValueError('Preview is already closed')

        self.alive = False

        self._cancel_step()

        self._cam.release()

    @property
    def fps(self) -> float:
        if self._frame_interval == 0:
            return float('inf')

        return 1/self._frame_interval

    @fps.setter
    def fps(self, value: float) -> None:
        if value == 0:
            self._frame_interval = -1
        elif value is None:
            self._frame_interval = 0
        else:
            self._frame_interval = 1 / value

        self._reset_step()
