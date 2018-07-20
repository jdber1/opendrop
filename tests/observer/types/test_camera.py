import asyncio
import time
from copy import copy
from unittest.mock import Mock, patch

import numpy as np
import pytest
from pytest import raises

from opendrop.observer.bases import Observation
from opendrop.observer.types.camera import ICamera, CameraObserver, CameraObserverPreview, CameraObservation
from opendrop.utility.resources import ResourceToken


# So PyCharm recognizes this file as a test file
def test_stub():
    pass


def create_my_camera_cls():
    class MyCamera(ICamera):
        init_count = 0
        teardown_count = 0

        IMAGE = np.array([[1, 2, 3]])

        def __init__(self):
            MyCamera.init_count += 1

        def capture(self):
            return self.IMAGE

        def teardown(self):
            MyCamera.teardown_count += 1

    return MyCamera


class TestCameraObserver:
    def setup(self):
        self.cam_cls = create_my_camera_cls()
        self.cam_token = ResourceToken(self.cam_cls)
        self.cam_observer = CameraObserver(self.cam_token)

    @pytest.mark.asyncio
    async def test_timelapse(self):
        NUM_FRAMES = 3
        FRAME_INTERVAL = 0.5

        EPSILON = 0.1

        timestamps = np.arange(0, NUM_FRAMES) * FRAME_INTERVAL

        observations = self.cam_observer.timelapse(timestamps)

        assert all(isinstance(o, Observation) for o in observations)
        assert len(observations) == len(timestamps)

        # Test time until ready
        for o, t in zip(observations, timestamps):
            assert abs(o.time_until_ready - t) < EPSILON

        loaded_at = []

        assert self.cam_cls.init_count == 1

        for i, o in enumerate(observations):
            # Make sure the camera resource hasn't been released midway through the timelapse
            assert self.cam_cls.teardown_count == 0

            im = await o

            # Make sure the image returned matches the predefined image
            assert (im == self.cam_cls.IMAGE).all()

            loaded_at.append(time.time())

        # Sleep for a short period, enough for the camera to have been released
        await asyncio.sleep(0.001)

        # Make sure the camera resource is released after the timelapse has finished collecting
        assert self.cam_cls.teardown_count == 1

        # Calculate the observation intervals
        loaded_at = np.array(loaded_at)
        deltas = loaded_at[1:] - loaded_at[:-1]

        assert (np.fabs(deltas - FRAME_INTERVAL) < EPSILON).all()

    # This unit test doesn't really belong in this class, so, todo: refactor
    @pytest.mark.asyncio
    async def test_cancel_camera_observation(self):
        load_from_cam_called = False

        def load_from_cam_wrapper(self):
            nonlocal load_from_cam_called
            load_from_cam_called = True

        with patch.object(CameraObservation, '_load_from_cam', load_from_cam_wrapper):
            observation = self.cam_observer.timelapse([0])[0]

            assert self.cam_cls.init_count == 1
            assert self.cam_cls.teardown_count == 0

            assert not observation.cancelled

            observation.cancel()

            assert observation.cancelled

            assert self.cam_cls.teardown_count == 1

            await asyncio.sleep(0.1)

            assert not load_from_cam_called


class TestCameraObserverPreview:
    def setup(self):
        self.cam_cls = create_my_camera_cls()
        self.cam_token = ResourceToken(self.cam_cls)
        self.cam_observer = CameraObserver(self.cam_token)
        self.cam_preview = CameraObserverPreview(self.cam_observer)

    @pytest.mark.asyncio
    async def test_on_changed(self):
        # Set `fps` to None, i.e. maximum fps
        self.cam_preview.fps = None

        checkpoints = []

        def cb():
            checkpoints.append(
                ('cb', copy(self.cam_preview.buffer))
            )

        self.cam_preview.on_changed.connect(cb)

        # Wait a short period so 'on_changed' is fired
        await asyncio.sleep(0.01)

        assert checkpoints[0][0] == 'cb'
        assert (checkpoints[0][1] == self.cam_cls.IMAGE).all()

    @pytest.mark.asyncio
    async def test_fps(self):
        EPSILON = 0.01

        FPS = [30, 0]
        WAIT = [0.5] * len(FPS)

        def cb():
            nonlocal num_frames

            num_frames += 1

        self.cam_preview.on_changed.connect(cb)

        for wait, fps in zip(WAIT, FPS):
            self.cam_preview.fps = fps
            num_frames = 0

            await asyncio.sleep(wait)

            assert abs(num_frames - fps * wait) <= max(fps * EPSILON, 1)  # minimum epsilon of 1 frame for wiggle room

    @pytest.mark.asyncio
    async def test_close(self):
        EPSILON = 0.1

        self.cam_preview.close()

        # Trying to close an already closed preview should raise an exception
        with raises(ValueError):
            self.cam_preview.close()

        # Changing the fps shouldn't 're-enable' the preview
        self.cam_preview.fps = None

        cb = Mock()

        self.cam_preview.on_changed.connect(cb)

        # Wait a short period of time so 'on_changed' has a chance of being fired
        await asyncio.sleep(EPSILON)

        cb.assert_not_called()

        # Make sure that camera resource is released after preview is closed
        assert self.cam_cls.teardown_count == 1

    def teardown(self):
        if self.cam_preview.alive:
            self.cam_preview.close()


class TestCameraObservation:
    def setup(self):
        self.cam_cls = create_my_camera_cls()
        self.cam_token = ResourceToken(self.cam_cls)
        self.cam_observer = CameraObserver(self.cam_token)

        self.o = self.cam_observer.timelapse([0])[0]

    def test_cancel(self):
        assert self.cam_cls.teardown_count == 0
        self.o.cancel()
        assert self.cam_cls.teardown_count == 1

    @pytest.mark.asyncio
    async def test_cancel_after_loaded(self):
        await self.o

        self.o.cancel()
