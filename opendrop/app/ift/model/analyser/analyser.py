import asyncio
import math
import time
from asyncio import Future
from enum import Enum
from operator import attrgetter
from typing import Tuple, Callable, Optional, Union, Iterable, Type, Sequence, Any

import numpy as np

from opendrop import sityping as si
from opendrop.app.common.model.image_acquisition.image_acquisition import ScheduledImage
from opendrop.app.common.model.operation import Operation, OperationGroup
from opendrop.iftcalc import phys_props
from opendrop.iftcalc.younglaplace.yl_fit import YoungLaplaceFit
from opendrop.mytypes import Image
from opendrop.utility.bindable.bindable import AtomicBindableAdapter, AtomicBindable, AtomicBindableVar
from opendrop.utility.events import Event
from .container import IFTPhysicalParameters, IFTImageAnnotations


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


# Classes

class IFTDropAnalysis(Operation):
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

    def __init__(self, scheduled_image: ScheduledImage, annotate_image: Callable[[Image], IFTImageAnnotations],
                 phys_params: IFTPhysicalParameters,
                 *,  # Dependency injection stuff
                 create_yl_fit: Type[YoungLaplaceFit] = YoungLaplaceFit,
                 calculate_ift: Callable = phys_props.calculate_ift,
                 calculate_volume: Callable = phys_props.calculate_volume,
                 calculate_surface_area: Callable = phys_props.calculate_surface_area,
                 calculate_worthington: Callable = phys_props.calculate_worthington) -> None:
        self._loop = asyncio.get_event_loop()

        self._time_start = time.time()

        self._scheduled_image = scheduled_image
        self._annotate_image = annotate_image

        self._loop.create_task(self._scheduled_image.read()).add_done_callback(self._hdl_scheduled_img_read)
        self.phys_params = phys_params

        self._start_fit_task = None  # type: Optional[asyncio.Task]

        # Dependency injection stuff
        self._create_yl_fit = create_yl_fit
        self._calculate_ift = calculate_ift
        self._calculate_volume = calculate_volume
        self._calculate_surface_area = calculate_surface_area
        self._calculate_worthington = calculate_worthington

        self._status_ = IFTDropAnalysis.Status.WAITING_FOR_IMAGE
        self.bn_status = AtomicBindableAdapter(lambda: self._status_)

        self._image = None  # type: Optional[Image]
        self.bn_image = AtomicBindableAdapter(lambda: self._image)

        self._image_annotations = None  # type: Optional[IFTImageAnnotations]
        self.bn_image_annotations = AtomicBindableAdapter(lambda: self._image_annotations)

        # The time (in Unix time) that the image was captured.
        self._image_timestamp = math.nan  # type: float
        self.bn_image_timestamp = AtomicBindableAdapter(lambda: self._image_timestamp)

        self._yl_fit_ = None  # type: Optional[YoungLaplaceFit]

        # Outputs
        self.bn_objective = AtomicBindableAdapter(self._get_objective)
        self.bn_bond_number = AtomicBindableAdapter(self._get_bond_number)
        self.bn_apex_coords_px = AtomicBindableAdapter(self._get_apex_coords_px)
        self.bn_apex_radius = AtomicBindableAdapter(self._get_apex_radius)
        self.bn_apex_rot = AtomicBindableAdapter(self._get_apex_rot)
        self.bn_interfacial_tension = AtomicBindableAdapter(self._get_interfacial_tension)
        self.bn_volume = AtomicBindableAdapter(self._get_volume)
        self.bn_surface_area = AtomicBindableAdapter(self._get_surface_area)
        self.bn_worthington = AtomicBindableAdapter(self._get_worthington)

        self.on_drop_contour_fit_changed = Event()

        # Log
        self.bn_log = AtomicBindableVar('')
        self._log_shim = self.LogShim(write=lambda s: self.bn_log.set(self.bn_log.get() + s))

        # Operation attributes
        self.bn_done = AtomicBindableAdapter(self._get_done)
        self.bn_progress = AtomicBindableAdapter(self._get_progress)
        self.bn_time_start = AtomicBindableAdapter(self._get_time_start)
        self.bn_time_est_complete = AtomicBindableAdapter(self._get_time_est_complete)

        self.bn_status.on_changed.connect(self.bn_done.poke)
        self.bn_status.on_changed.connect(self.bn_progress.poke)

    # Property adapters for bindables (type annotations are not strictly correct but is a bit of a hack to allow PyCharm
    # recognise the types)
    status = AtomicBindable.property_adapter(attrgetter('bn_status'))  # type: IFTDropAnalysis.Status
    image = AtomicBindable.property_adapter(attrgetter('bn_image'))  # type: Image
    image_annotations = AtomicBindable.property_adapter(attrgetter('bn_image_annotations'))  # type: IFTImageAnnotations
    image_timestamp = AtomicBindable.property_adapter(attrgetter('bn_image_timestamp'))  # type: float
    objective = AtomicBindable.property_adapter(attrgetter('bn_objective'))  # type: float
    bond_number = AtomicBindable.property_adapter(attrgetter('bn_bond_number'))  # type: float
    apex_coords_px = AtomicBindable.property_adapter(attrgetter('bn_apex_coords_px'))  # type: Tuple[int, int]
    apex_radius = AtomicBindable.property_adapter(attrgetter('bn_apex_radius'))  # type: si.Length
    apex_rot = AtomicBindable.property_adapter(attrgetter('bn_apex_rot'))  # type: float
    interfacial_tension = AtomicBindable.property_adapter(attrgetter('bn_interfacial_tension'))  # type: si.SurfaceTension
    volume = AtomicBindable.property_adapter(attrgetter('bn_volume'))  # type: si.Volume
    surface_area = AtomicBindable.property_adapter(attrgetter('bn_surface_area'))  # type: si.Area
    worthington = AtomicBindable.property_adapter(attrgetter('bn_worthington'))  # type: float
    log = AtomicBindable.property_adapter(attrgetter('bn_log'))  # type: str

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

    def _hdl_scheduled_img_read(self, read_task: Future) -> None:
        if read_task.cancelled():
            self.cancel()
            return

        if self.bn_done.get():
            return

        image, image_timestamp = read_task.result()
        self._give_image(image, image_timestamp, self._annotate_image(image))
        self._start_fit_task = self._loop.create_task(self._start_fit())

    def _give_image(self, image: Image, image_timestamp: float, image_annotations: IFTImageAnnotations) -> None:
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

    async def _start_fit(self) -> None:
        if self._status is not self.Status.READY_TO_FIT:
            raise ValueError("Can't perform _start_fit(), requires current status to be {}, but is actually {}"
                             .format(self.Status.READY_TO_FIT, self._status))

        image_annotations = self._image_annotations
        drop_contour_px = image_annotations.drop_contour_px
        drop_contour_px = bl_tl_coords_swap(self._image.shape[0], *drop_contour_px.T).T

        if self._is_sessile:
            drop_contour_px[:, 1] *= -1

        self._yl_fit = self._create_yl_fit(drop_contour_px, self._log_shim)
        self._status = IFTDropAnalysis.Status.FITTING

        await self._yl_fit.optimise()

        stop_flags = self._yl_fit.stop_flags

        if stop_flags & YoungLaplaceFit.StopFlag.UNEXPECTED_EXCEPTION != 0:
            self._status = IFTDropAnalysis.Status.UNEXPECTED_EXCEPTION
        elif stop_flags & YoungLaplaceFit.StopFlag.CANCELLED != 0:
            self._status = IFTDropAnalysis.Status.CANCELLED
        else:
            self._status = IFTDropAnalysis.Status.FINISHED

    def cancel(self) -> None:
        if self._status.terminal:
            # This is already at the end of its life.
            return

        if self._yl_fit is not None:
            self._yl_fit.cancel()
            # This status will be changed to CANCELLED after _yl_fit is cancelled.
        else:
            self._status = self.Status.CANCELLED

    def generate_drop_contour_fit(self, samples: int = 50) -> Optional[np.ndarray]:
        yl_fit = self._yl_fit
        if yl_fit is None:
            return None

        s = np.linspace(-yl_fit.profile_domain, yl_fit.profile_domain, samples)

        s_right = s[s >= 0]
        s_left = s[s < 0]

        # The 'profile' only has data points for one side (positive r side) of the drop
        contour_right_rz = yl_fit.profile(s_right)[:, :2]

        # so we need to mirror its r coordinates to get the other side
        contour_left_rz = (yl_fit.profile(-s_left)[:, :2]) * (-1, 1)

        # and combine both sides to get the full contour.
        contour_rz = np.empty(s.shape + (2,), dtype=float)
        contour_rz[s >= 0] = contour_right_rz
        contour_rz[s < 0] = contour_left_rz

        # Scale the contour to the right size.
        contour_rz *= yl_fit.apex_radius

        # Convert from rz coordinates to xy coordinates, same coordinate system as original contour passed to
        # YoungLaplaceFit.__init__().
        contour_xy = yl_fit.xy_from_rz(*contour_rz.T).T
        contour_xy += (yl_fit.apex_x, yl_fit.apex_y)

        if self._is_sessile:
            contour_xy[:, 1] *= -1

        contour_xy = bl_tl_coords_swap(self._image.shape[0], *contour_xy.T).T
        contour_xy -= self._get_apex_coords_px()

        return contour_xy

    @property
    def _is_sessile(self) -> bool:
        return self.phys_params.inner_density < self.phys_params.outer_density

    @property
    def _status(self) -> 'IFTDropAnalysis.Status':
        return self._status_

    @_status.setter
    def _status(self, new_status: 'IFTDropAnalysis.Status') -> None:
        self._status_ = new_status
        self.bn_status.poke()

    @property
    def _yl_fit(self) -> YoungLaplaceFit:
        return self._yl_fit_

    @_yl_fit.setter
    def _yl_fit(self, yl_fit: YoungLaplaceFit) -> None:
        assert self._yl_fit is None

        self._yl_fit_ = yl_fit
        self._yl_fit_.on_params_changed.connect(self._hdl_yl_fit_params_changed)

    @property
    def drop_contour_fit_residuals(self) -> Optional[np.ndarray]:
        yl_fit = self._yl_fit
        if yl_fit is None:
            return None

        return yl_fit.residuals

    def _hdl_yl_fit_params_changed(self) -> None:
        self.bn_objective.poke()
        self.bn_bond_number.poke()
        self.bn_interfacial_tension.poke()
        self.bn_volume.poke()
        self.bn_surface_area.poke()
        self.bn_worthington.poke()
        self.bn_apex_coords_px.poke()
        self.bn_apex_radius.poke()
        self.bn_apex_rot.poke()
        self.on_drop_contour_fit_changed.fire()

    def _get_bond_number(self) -> float:
        yl_fit = self._yl_fit
        if yl_fit is None:
            return math.nan

        return yl_fit.bond_number

    def _get_interfacial_tension(self) -> si.SurfaceTension:
        yl_fit = self._yl_fit
        if yl_fit is None:
            return math.nan

        inner_density = self.phys_params.inner_density  # type: si.Density
        outer_density = self.phys_params.outer_density  # type: si.Density
        gravity = self.phys_params.gravity  # type: si.Acceleration

        bond_number = self._get_bond_number()
        apex_radius = self._get_apex_radius()  # type: si.Length

        return self._calculate_ift(inner_density, outer_density, bond_number, apex_radius, gravity)

    def _get_volume(self) -> si.Volume:
        yl_fit = self._yl_fit
        if yl_fit is None:
            return math.nan

        profile_domain = yl_fit.profile_domain

        bond_number = self._get_bond_number()
        apex_radius = self._get_apex_radius()  # type: si.Length

        return self._calculate_volume(profile_domain, bond_number, apex_radius)

    def _get_surface_area(self) -> si.Area:
        yl_fit = self._yl_fit
        if yl_fit is None:
            return math.nan

        profile_size = yl_fit.profile_domain

        bond_number = self._get_bond_number()
        apex_radius = self._get_apex_radius()  # type: si.Length

        return self._calculate_surface_area(profile_size, bond_number, apex_radius)

    def _get_worthington(self) -> float:
        yl_fit = self._yl_fit
        if yl_fit is None:
            return math.nan

        inner_density = self.phys_params.inner_density  # type: si.Density
        outer_density = self.phys_params.outer_density  # type: si.Density
        needle_width = self.phys_params.needle_width  # type: si.Length
        gravity = self.phys_params.gravity  # type: si.Acceleration
        ift = self._get_interfacial_tension()
        volume = self._get_volume()

        return self._calculate_worthington(inner_density, outer_density, gravity, ift, volume, needle_width)

    def _get_objective(self) -> float:
        yl_fit = self._yl_fit
        if yl_fit is None:
            return math.nan

        return yl_fit.objective

    def _get_apex_coords_px(self) -> Tuple[float, float]:
        yl_fit = self._yl_fit
        if yl_fit is None:
            return (math.nan, math.nan)

        if not self._is_sessile:
            apex_coords = yl_fit.apex_x, yl_fit.apex_y
        else:
            apex_coords = yl_fit.apex_x, -yl_fit.apex_y

        # Convert to image coordinates
        apex_coords = bl_tl_coords_swap(self._image.shape[0], *apex_coords).astype(int)

        return tuple(apex_coords)

    def _get_apex_radius(self) -> si.Length:
        yl_fit = self._yl_fit
        if yl_fit is None:
            return math.nan

        apex_radius_px = self._yl_fit.apex_radius
        m_per_px = self._image_annotations.m_per_px

        return apex_radius_px * m_per_px

    def _get_apex_rot(self) -> float:
        yl_fit = self._yl_fit
        if yl_fit is None:
            return math.nan

        # Negate so that positive angle is counter-clockwise.
        angle = -yl_fit.apex_rot

        if self._is_sessile:
            angle *= -1

        return angle


class IFTAnalysis(OperationGroup):
    def __init__(self, scheduled_images: Sequence[ScheduledImage],
                 annotate_image: Callable[[Image], IFTImageAnnotations], phys_params: IFTPhysicalParameters) -> None:
        self.drop_analyses = []
        for scheduled_img in scheduled_images:
            self.drop_analyses.append(IFTDropAnalysis(
                scheduled_image=scheduled_img,
                annotate_image=annotate_image,
                phys_params=phys_params
            ))

        super().__init__(operations=self.drop_analyses)

        self.bn_cancelled = AtomicBindableVar(False)

    def cancel(self) -> None:
        if self.bn_done.get():
            return
        super().cancel()
        self.bn_cancelled.set(True)
