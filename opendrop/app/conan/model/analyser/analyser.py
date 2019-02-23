import asyncio
import math
import time
from asyncio import Future
from enum import Enum
from operator import attrgetter
from typing import Callable, Optional, Sequence, Any, Union, Iterable

import numpy as np

from opendrop.app.common.model.image_acquisition.image_acquisition import ScheduledImage
from opendrop.app.common.model.operation import Operation, OperationGroup
from opendrop.conancalc.conancalc import ContactAngleCalculator
from opendrop.mytypes import Image
from opendrop.utility.bindable.bindable import AtomicBindableAdapter, AtomicBindable, AtomicBindableVar
from opendrop.utility.geometry import Line2, Vector2
from .container import ConanImageAnnotations


# Helper functions

def bl_tl_coords_swap(height: float, x: Union[float, Iterable[float]], y: Union[float, Iterable[float]]) -> np.ndarray:
    """
    This function is used to convert coordinates from a 'top-left' origin system with x increasing 'rightwards' and
    y increasing 'downwards' (such as those commonly used in graphics), to a coordinate system with a 'bottom-left'
    origin system, with x still increasing 'rightwards' but with y increasing 'upwards' (such as those commonly used in
    mathematics). Or vice versa.
    """
    x, y = np.array((x, y))
    return np.array((x, height - y))


def bl_tl_poly1d_swap(height: float, poly: np.poly1d) -> np.poly1d:
    poly_c = poly.coefficients
    poly_c[-1] = height - poly_c[-1]
    poly_c[:-1] *= -1

    return np.poly1d(poly_c)


# Classes

class ConanDropAnalysis(Operation):
    class Status(Enum):
        WAITING_FOR_IMAGE = ('Waiting for image', False)
        READY_TO_FIT = ('Ready to fit', False)
        FITTING = ('Fitting', False)
        FINISHED = ('Finished', True)
        CANCELLED = ('Cancelled', True)
        UNEXPECTED_EXCEPTION = ('Unexpected exception', True)

        def __init__(self, friendly: str, terminal: bool) -> None:
            self.friendly = friendly
            self.terminal = terminal

        def __str__(self) -> str:
            return self.friendly

    class LogShim:
        def __init__(self, write: Callable[[str], Any]) -> None:
            self.write = write

    def __init__(self, scheduled_image: ScheduledImage, annotate_image: Callable[[Image], ConanImageAnnotations]) \
            -> None:
        self._loop = asyncio.get_event_loop()

        self._time_start = time.time()

        self._scheduled_image = scheduled_image
        self._annotate_image = annotate_image

        self._loop.create_task(self._scheduled_image.read()).add_done_callback(self._hdl_scheduled_img_read)

        self._status_value = self.Status.WAITING_FOR_IMAGE
        self.bn_status = AtomicBindableAdapter(lambda: self._status_value)

        self._image = None  # type: Optional[Image]
        self.bn_image = AtomicBindableAdapter(lambda: self._image)

        # The time (in Unix time) that the image was captured.
        self._image_timestamp = math.nan  # type: float
        self.bn_image_timestamp = AtomicBindableAdapter(lambda: self._image_timestamp)

        self._image_annotations = None  # type: Optional[ConanImageAnnotations]
        self.bn_image_annotations = AtomicBindableAdapter(lambda: self._image_annotations)

        self._conan_calc_value = None  # type: Optional[ContactAngleCalculator]

        self.bn_left_tangent = AtomicBindableAdapter(self._get_left_tangent)
        self.bn_left_angle = AtomicBindableAdapter(self._get_left_angle)
        self.bn_left_point = AtomicBindableAdapter(self._get_left_point)

        self.bn_right_tangent = AtomicBindableAdapter(self._get_right_tangent)
        self.bn_right_angle = AtomicBindableAdapter(self._get_right_angle)
        self.bn_right_point = AtomicBindableAdapter(self._get_right_point)

        # Log
        self.bn_log = AtomicBindableVar('')
        self._log_shim = self.LogShim(write=lambda s: self.bn_log.set(self.bn_log.get() + s))

        # Operation attributes
        self.bn_done = AtomicBindableAdapter(self._get_done)
        self.bn_canceleld = AtomicBindableAdapter(lambda: self.status is self.Status.CANCELLED)
        self.bn_progress = AtomicBindableAdapter(self._get_progress)
        self.bn_time_start = AtomicBindableAdapter(self._get_time_start)
        self.bn_time_est_complete = AtomicBindableAdapter(self._get_time_est_complete)

        self.bn_status.on_changed.connect(self.bn_done.poke)
        self.bn_status.on_changed.connect(self.bn_progress.poke)

    # Property adapters for bindables (type annotations are not strictly correct but is a bit of a hack to allow PyCharm
    # recognise the types)
    status = AtomicBindable.property_adapter(attrgetter('bn_status'))  # type: Status
    image = AtomicBindable.property_adapter(attrgetter('bn_image'))  # type: Image
    image_annotations = AtomicBindable.property_adapter(attrgetter('bn_image_annotations'))  # type: ConanImageAnnotations
    image_timestamp = AtomicBindable.property_adapter(attrgetter('bn_image_timestamp'))  # type: float
    log = AtomicBindable.property_adapter(attrgetter('bn_log'))  # type: str

    def _hdl_scheduled_img_read(self, read_task: Future) -> None:
        if read_task.cancelled():
            self.cancel()
            return

        if self.bn_done.get():
            return

        image, image_timestamp = read_task.result()
        self._give_image(image, image_timestamp, self._annotate_image(image))
        self._start_fit()

    def _give_image(self, image: Image, image_timestamp: float, image_annotations: ConanImageAnnotations) -> None:
        if self._status is not self.Status.WAITING_FOR_IMAGE:
            raise ValueError("Can't perform _give_image(), requires current status to be {}, but is actually {}"
                             .format(self.Status.WAITING_FOR_IMAGE, self._status))

        assert self._image is self._image_annotations is None

        self._image = image
        self._image_timestamp = image_timestamp
        self._image_annotations = image_annotations

        # Set given image to be readonly to prevent bugs.
        self._image.flags.writeable = False

        self._status = self.Status.READY_TO_FIT

        self.bn_image.poke()
        self.bn_image_timestamp.poke()
        self.bn_image_annotations.poke()

    def _start_fit(self) -> None:
        if self._status is not self.Status.READY_TO_FIT:
            raise ValueError("Can't perform _start_fit(), requires current status to be {}, but is actually {}"
                             .format(self.Status.READY_TO_FIT, self._status))

        self._status = self.Status.FITTING

        image = self._image
        drop_contours = self._image_annotations.drop_contours_px
        surface_line = self._image_annotations.surface_line_px

        # Convert to coordinates where y-increases upwards.
        drop_contours = bl_tl_coords_swap(image.shape[0], *drop_contours.T).T

        surface_line_p0, surface_line_p1 = bl_tl_coords_swap(image.shape[0], *zip(surface_line.p0, surface_line.p1)).T
        surface_line = Line2(p0=surface_line_p0, p1=surface_line_p1)

        surface_poly = np.poly1d((surface_line.gradient, surface_line.eval_at(x=0).y))

        self._conan_calc = ContactAngleCalculator(drop_contours, surface_poly)

        self._status = self.Status.FINISHED

    @property
    def _conan_calc(self) -> ContactAngleCalculator:
        return self._conan_calc_value

    @_conan_calc.setter
    def _conan_calc(self, value: ContactAngleCalculator) -> None:
        assert self._conan_calc is None
        self._conan_calc_value = value
        self._conan_calc.on_params_changed.connect(self._hdl_conan_calc_params_changed)
        self._hdl_conan_calc_params_changed()

    def _get_left_tangent(self) -> np.poly1d:
        if self._conan_calc is None:
            return np.poly1d((math.nan, math.nan))

        image_height = self._image.shape[0]
        left_tangent = self._conan_calc.left_tangent
        left_tangent = bl_tl_poly1d_swap(image_height, left_tangent)

        return left_tangent

    def _get_right_tangent(self) -> np.poly1d:
        if self._conan_calc is None:
            return np.poly1d((math.nan, math.nan))

        image_height = self._image.shape[0]
        right_tangent = self._conan_calc.right_tangent
        right_tangent = bl_tl_poly1d_swap(image_height, right_tangent)

        return right_tangent

    def _get_left_angle(self) -> float:
        if self._conan_calc is None:
            return math.nan

        return self._conan_calc.left_angle

    def _get_right_angle(self) -> float:
        if self._conan_calc is None:
            return math.nan

        return self._conan_calc.right_angle

    def _get_left_point(self) -> Vector2[float]:
        if self._conan_calc is None:
            return Vector2(math.nan, math.nan)

        image_height = self._image.shape[0]

        left_point = self._conan_calc.left_point
        left_point = Vector2(*bl_tl_coords_swap(image_height, left_point.x, left_point.y))

        return left_point

    def _get_right_point(self) -> Vector2[float]:
        if self._conan_calc is None:
            return Vector2(math.nan, math.nan)

        image_height = self._image.shape[0]

        right_point = self._conan_calc.right_point
        right_point = Vector2(*bl_tl_coords_swap(image_height, right_point.x, right_point.y))

        return right_point

    def _hdl_conan_calc_params_changed(self) -> None:
        self.bn_left_tangent.poke()
        self.bn_left_angle.poke()
        self.bn_left_point.poke()

        self.bn_right_tangent.poke()
        self.bn_right_angle.poke()
        self.bn_right_point.poke()

    def _get_done(self) -> bool:
        return self.status.terminal

    def _get_progress(self) -> float:
        if self.bn_done.get():
            return 1
        else:
            return 0

    def _get_time_start(self) -> float:
        return self._time_start

    def _get_time_est_complete(self) -> float:
        return self._scheduled_image.est_ready

    def cancel(self) -> None:
        if self._status.terminal:
            # This is already at the end of its life.
            return

        self._status = self.Status.CANCELLED

    @property
    def _status(self) -> Status:
        return self._status_value

    @_status.setter
    def _status(self, new_status: Status) -> None:
        self._status_value = new_status
        self.bn_status.poke()


class ConanAnalysis(OperationGroup):
    def __init__(self, scheduled_images: Sequence[ScheduledImage],
                 annotate_image: Callable[[Image], ConanImageAnnotations]) -> None:
        self.drop_analyses = []
        for scheduled_img in scheduled_images:
            self.drop_analyses.append(ConanDropAnalysis(
                scheduled_image=scheduled_img,
                annotate_image=annotate_image,
            ))

        super().__init__(operations=self.drop_analyses)
