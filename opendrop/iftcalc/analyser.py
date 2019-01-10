import io
import math
from enum import Enum
from operator import attrgetter
from typing import Tuple, Callable, Optional, IO, Union, Iterable, Type

import numpy as np

from opendrop.mytypes import Image
from opendrop.utility.bindable.bindable import AtomicBindableAdapter, AtomicBindable
from . import phys_props
from opendrop import si_typing as si
from .types import IFTPhysicalParameters, IFTImageAnnotations
from .younglaplace.yl_fit import YoungLaplaceFit


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


class IFTDropAnalysis:
    class Status(Enum):
        # The first element of the tuples are just to keep each enum unique.
        WAITING_FOR_IMAGE = (0, False)
        READY_TO_FIT = (1, False)
        FITTING = (2, False)
        FINISHED = (3, True)
        CANCELLED = (4, True)
        UNEXPECTED_EXCEPTION = (5, True)

        def __init__(self, id_: int, terminal: bool) -> None:
            self.terminal = terminal

    def __init__(self, phys_params: IFTPhysicalParameters, create_yl_fit: Type[YoungLaplaceFit] = YoungLaplaceFit,
                 calculate_ift: Callable = phys_props.calculate_ift,
                 calculate_volume: Callable = phys_props.calculate_volume,
                 calculate_surface_area: Callable = phys_props.calculate_surface_area,
                 calculate_worthington: Callable = phys_props.calculate_worthington) -> None:
        self._phys_params = phys_params

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
        self._image_timestamp = None  # type: Optional[float]
        self.bn_image_timestamp = AtomicBindableAdapter(lambda: self._image_timestamp)

        self._yl_fit_ = None  # type: Optional[YoungLaplaceFit]

        # Outputs
        self.bn_objective = AtomicBindableAdapter(self._get_objective)
        self.bn_bond_number = AtomicBindableAdapter(self._get_bond_number)
        self.bn_apex_pos_px = AtomicBindableAdapter(self._get_apex_pos_px)
        self.bn_apex_radius = AtomicBindableAdapter(self._get_apex_radius)
        self.bn_apex_rot = AtomicBindableAdapter(self._get_apex_rot)
        self.bn_interfacial_tension = AtomicBindableAdapter(self._get_interfacial_tension)
        self.bn_volume = AtomicBindableAdapter(self._get_volume)
        self.bn_surface_area = AtomicBindableAdapter(self._get_surface_area)
        self.bn_worthington = AtomicBindableAdapter(self._get_worthington)
        self.bn_drop_contour_fit = AtomicBindableAdapter(self.generate_drop_contour_fit)
        self.bn_drop_contour_fit_residuals = AtomicBindableAdapter(self._get_drop_contour_fit_residuals)

        # Log
        self._log = io.StringIO()

    status = AtomicBindable.property_adapter(attrgetter('bn_status'))

    def _give_image(self, image: Image, image_timestamp: float, image_annotations: IFTImageAnnotations) -> None:
        if self._status is not self.Status.WAITING_FOR_IMAGE:
            raise ValueError("Can't perform _give_image(), requires current status to be {}, but is actually {}"
                             .format(self.Status.WAITING_FOR_IMAGE, self._status))

        assert self._image is self._image_annotations is None

        self._image = image
        self._image_timestamp = image_timestamp
        self._image_annotations = image_annotations

        self._status = self.Status.READY_TO_FIT

        self.bn_image.poke()
        self.bn_image_timestamp.poke()
        self.bn_image_annotations.poke()

    async def _start_fit(self) -> None:
        if self._status is not self.Status.READY_TO_FIT:
            raise ValueError("Can't perform _start_fit(), requires current status to be {}, but is actually {}"
                             .format(self.Status.READY_TO_FIT, self._status))

        image_annotations = self._image_annotations

        # Drop contour, in units of metres
        drop_region_height = image_annotations.drop_region_px.h

        drop_contour_px = image_annotations.drop_contour_px
        drop_contour_px = bl_tl_coords_swap(drop_region_height, *drop_contour_px.T).T

        self._yl_fit = self._create_yl_fit(drop_contour_px, self._log)
        self._status = IFTDropAnalysis.Status.FITTING

        await self._yl_fit.optimise()

        stop_flags = self._yl_fit.stop_flags

        if stop_flags & YoungLaplaceFit.StopFlag.UNEXPECTED_EXCEPTION != 0:
            self._status = IFTDropAnalysis.Status.UNEXPECTED_EXCEPTION
        elif stop_flags & YoungLaplaceFit.StopFlag.CANCELLED != 0:
            self._status = IFTDropAnalysis.Status.CANCELLED
        else:
            self._status = IFTDropAnalysis.Status.FINISHED

    def _hdl_yl_fit_status_changed(self) -> None:
        yl_fit_status = self._yl_fit.status
        if yl_fit_status is YoungLaplaceFit.Status.FINISHED:
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

    def generate_drop_contour_fit(self, samples: int = 200) -> Optional[np.ndarray]:
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

        drop_region_px = self._image_annotations.drop_region_px
        contour_xy = bl_tl_coords_swap(drop_region_px.h, *contour_xy.T).T
        contour_xy += drop_region_px.pos
        contour_xy -= self._get_apex_pos_px()

        return contour_xy

    @property
    def log(self) -> IO:
        return self._log

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
    def _yl_fit(self, yl_fit: YoungLaplaceFit) -> YoungLaplaceFit:
        assert self._yl_fit is None

        self._yl_fit_ = yl_fit
        self._yl_fit_.on_params_changed.connect(self._hdl_yl_fit_params_changed, immediate=True)

    def _hdl_yl_fit_params_changed(self) -> None:
        self.bn_objective.poke()
        self.bn_bond_number.poke()
        self.bn_interfacial_tension.poke()
        self.bn_volume.poke()
        self.bn_surface_area.poke()
        self.bn_worthington.poke()
        self.bn_apex_pos_px.poke()
        self.bn_apex_radius.poke()
        self.bn_apex_rot.poke()
        self.bn_drop_contour_fit.poke()
        self.bn_drop_contour_fit_residuals.poke()

    def _get_bond_number(self) -> float:
        yl_fit = self._yl_fit
        if yl_fit is None:
            return math.nan

        return yl_fit.bond_number

    def _get_interfacial_tension(self) -> si.SurfaceTension:
        yl_fit = self._yl_fit
        if yl_fit is None:
            return math.nan

        inner_density = self._phys_params.inner_density  # type: si.Density
        outer_density = self._phys_params.outer_density  # type: si.Density
        gravity = self._phys_params.gravity  # type: si.Acceleration

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

        inner_density = self._phys_params.inner_density  # type: si.Density
        outer_density = self._phys_params.outer_density  # type: si.Density
        needle_width = self._phys_params.needle_width  # type: si.Length
        gravity = self._phys_params.gravity  # type: si.Acceleration
        ift = self._get_interfacial_tension()
        volume = self._get_volume()

        return self._calculate_worthington(inner_density, outer_density, gravity, ift, volume, needle_width)

    def _get_objective(self) -> float:
        yl_fit = self._yl_fit
        if yl_fit is None:
            return math.nan

        return yl_fit.objective

    def _get_apex_pos_px(self) -> Tuple[int, int]:
        yl_fit = self._yl_fit
        if yl_fit is None:
            return math.nan

        apex_pos = yl_fit.apex_x, yl_fit.apex_y

        # Convert to image coordinates
        drop_region_px = self._image_annotations.drop_region_px
        apex_pos = bl_tl_coords_swap(drop_region_px.h, *apex_pos).astype(int)
        apex_pos += drop_region_px.pos

        return tuple(apex_pos)

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

        return yl_fit.apex_rot

    def _get_drop_contour_fit_residuals(self) -> Optional[np.ndarray]:
        yl_fit = self._yl_fit
        if yl_fit is None:
            return None

        return yl_fit.residuals
