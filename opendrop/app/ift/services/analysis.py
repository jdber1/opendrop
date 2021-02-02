# Copyright © 2020, Joseph Berry, Rico Tabor (opendrop.dev@gmail.com)
# OpenDrop is released under the GNU GPL License. You are free to
# modify and distribute the code, but always under the same license
# (i.e. you cannot make commercial derivatives).
#
# If you use this software in your research, please cite the following
# journal articles:
#
# J. D. Berry, M. J. Neeson, R. R. Dagastine, D. Y. C. Chan and
# R. F. Tabor, Measurement of surface and interfacial tension using
# pendant drop tensiometry. Journal of Colloid and Interface Science 454
# (2015) 226–237. https://doi.org/10.1016/j.jcis.2015.05.012
#
# E. Huang, T. Denning, A. Skoufis, J. Qi, R. R. Dagastine, R. F. Tabor
# and J. D. Berry, OpenDrop: Open-source software for pendant drop
# tensiometry & contact angle measurements, submitted to the Journal of
# Open Source Software
#
# These citations help us not only to understand who is using and
# developing OpenDrop, and for what purpose, but also to justify
# continued development of this code and other open source resources.
#
# OpenDrop is distributed WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.  You
# should have received a copy of the GNU General Public License along
# with this software.  If not, see <https://www.gnu.org/licenses/>.


import asyncio
import math
import time
from asyncio import Future
from enum import Enum
from typing import Optional
from injector import inject

import numpy as np

from opendrop.app.common.services.acquisition import InputImage
from opendrop.app.ift.services.edges import PendantEdgeDetectionParamsFactory, PendantEdgeDetectionService
from opendrop.app.ift.services.quantities import PendantPhysicalParamsFactory
from opendrop.app.ift.services.younglaplace import YoungLaplaceFitService, YoungLaplaceFitResult

from opendrop.fit.needle import needle_fit

from opendrop.utility.bindable import AccessorBindable, VariableBindable
from opendrop.utility.geometry import Vector2


PI = math.pi


class PendantAnalysisService:
    @inject
    def __init__(
            self,
            *,
            edge_det_params: PendantEdgeDetectionParamsFactory,
            edge_det_service: PendantEdgeDetectionService,
            ylfit_service: YoungLaplaceFitService,
            phys_params: PendantPhysicalParamsFactory,
    ) -> None:
        self._edge_det_params = edge_det_params
        self._edge_det_service = edge_det_service
        self._ylfit_service = ylfit_service
        self._phys_params = phys_params

    def analyse(self, image: InputImage) -> 'PendantAnalysisJob':
        return PendantAnalysisJob(
            image,
            edge_det_params=self._edge_det_params,
            edge_det_service=self._edge_det_service,
            ylfit_service=self._ylfit_service,
            phys_params=self._phys_params,
        )


class PendantAnalysisJob:
    class Status(Enum):
        WAITING_FOR_IMAGE = ('Waiting for image', False)
        FITTING = ('Fitting', False)
        FINISHED = ('Finished', True)
        CANCELLED = ('Cancelled', True)

        def __init__(self, display_name: str, is_terminal: bool) -> None:
            self.display_name = display_name
            self.is_terminal = is_terminal

        def __str__(self) -> str:
            return self.display_name

    def __init__(
            self,
            input_image: InputImage,
            *,
            edge_det_params: PendantEdgeDetectionParamsFactory,
            edge_det_service: PendantEdgeDetectionService,
            ylfit_service: YoungLaplaceFitService,
            phys_params: PendantPhysicalParamsFactory,
    ) -> None:
        self._loop = asyncio.get_event_loop()

        self._edge_det_params = edge_det_params
        self._phys_params = phys_params

        self._edge_det_service = edge_det_service
        self._ylfit_service = ylfit_service

        self._time_start = time.time()
        self._time_end = math.nan

        self._input_image = input_image

        self._status = self.Status.WAITING_FOR_IMAGE
        self.bn_status = AccessorBindable(
            getter=self._get_status,
            setter=self._set_status,
        )

        self._image = None  # type: Optional[np.ndarray]
        # The time (in Unix time) that the image was captured.
        self._image_timestamp = math.nan  # type: float

        self.bn_image = AccessorBindable(self._get_image)
        self.bn_image_timestamp = AccessorBindable(self._get_image_timestamp)

        # Attributes from YoungLaplaceFitter
        self.bn_bond_number = VariableBindable(math.nan)
        self.bn_apex_coords_px = VariableBindable(Vector2(math.nan, math.nan))
        self.bn_apex_radius_px = VariableBindable(math.nan)
        self.bn_rotation = VariableBindable(math.nan)
        self.bn_drop_profile_fit = VariableBindable(None)
        self.bn_residuals = VariableBindable(None)
        self.bn_arclengths = VariableBindable(None)

        # Attributes from PhysicalPropertiesCalculator
        self.bn_interfacial_tension = VariableBindable(math.nan)
        self.bn_volume = VariableBindable(math.nan)
        self.bn_surface_area = VariableBindable(math.nan)
        self.bn_apex_radius = VariableBindable(math.nan)
        self.bn_worthington = VariableBindable(math.nan)

        # Attributes from FeatureExtractor
        self.bn_drop_region = VariableBindable(None)
        self.bn_needle_region = VariableBindable(None)
        self.bn_drop_profile_extract = VariableBindable(None)
        self.bn_needle_profile_extract = VariableBindable(None)
        self.bn_needle_width_px = VariableBindable(math.nan)

        self.bn_is_done = AccessorBindable(getter=self._get_is_done)
        self.bn_is_cancelled = AccessorBindable(getter=self._get_is_cancelled)
        self.bn_progress = AccessorBindable(self._get_progress)
        self.bn_time_start = AccessorBindable(self._get_time_start)
        self.bn_time_est_complete = AccessorBindable(self._get_time_est_complete)

        self.bn_status.on_changed.connect(self.bn_is_done.poke)
        self.bn_status.on_changed.connect(self.bn_progress.poke)

        self._loop.create_task(self._input_image.read()).add_done_callback(self._hdl_input_image_read)

        self._extracted_features = None
        self._young_laplace_fit = None

    def _hdl_input_image_read(self, read_task: Future) -> None:
        if read_task.cancelled():
            self.cancel()
            return

        if self.bn_is_done.get():
            return

        image, image_timestamp = read_task.result()
        self._start_fit(image, image_timestamp)

    def _start_fit(self, image: np.ndarray, image_timestamp: float) -> None:
        assert self._image is None

        self._image = image
        self._image_timestamp = image_timestamp

        # Set given image to be readonly to prevent introducing some accidental bugs.
        self._image.flags.writeable = False

        edge_det_params = self._edge_det_params.create()
        self.bn_drop_region.set(edge_det_params.drop_region)
        self.bn_needle_region.set(edge_det_params.needle_region)

        self._extracted_features = self._edge_det_service.detect(image, edge_det_params)
        self._extracted_features.add_done_callback(self._edge_det_done)

        self.bn_image.poke()
        self.bn_image_timestamp.poke()

        self.bn_status.set(self.Status.FITTING)

    def _edge_det_done(self, fut: asyncio.Future) -> None:
        if fut.cancelled():
            self.cancel()
            return
        try:
            features = fut.result()
        except Exception as e:
            raise e

        self.bn_drop_profile_extract.set(features.drop_edge)
        self.bn_needle_profile_extract.set((features.needle_left_edge, features.needle_right_edge))

        needle_edge = np.concatenate((features.needle_left_edge, features.needle_right_edge))
        self.bn_needle_width_px.set(2 * needle_fit(needle_edge.T).radius)

        self._young_laplace_fit = self._ylfit_service.fit(features.drop_edge.T)
        self._young_laplace_fit.add_done_callback(self._young_laplace_fit_done)

    def _young_laplace_fit_done(self, fut: asyncio.Future) -> None:
        fit_result: YoungLaplaceFitResult

        if fut.cancelled():
            self.cancel()
            return
        try:
            fit_result = fut.result()
        except Exception as e:
            raise e

        phys_params = self._phys_params.create()

        needle_diameter_px = self.bn_needle_width_px.get()
        needle_diameter = phys_params.needle_diameter
        px_size = needle_diameter/needle_diameter_px

        bond = fit_result.bond
        radius_px = fit_result.radius
        apex_x = fit_result.apex_x
        apex_y = fit_result.apex_y
        rotation = fit_result.rotation
        residuals = fit_result.residuals
        closest = fit_result.closest
        arclengths = fit_result.arclengths
        surface_area_px = fit_result.surface_area
        volume_px = fit_result.volume

        gravity = phys_params.gravity
        drop_density = phys_params.drop_density
        continuous_density = phys_params.continuous_density

        radius = radius_px * px_size
        surface_area = surface_area_px * px_size**2
        volume = volume_px * px_size**3

        delta_density = abs(drop_density - continuous_density)
        ift = delta_density * gravity * radius**2 / bond
        worthington = (delta_density * gravity * volume) / (PI * ift * needle_diameter)

        self.bn_bond_number.set(bond)
        self.bn_apex_coords_px.set(Vector2(apex_x, apex_y))
        self.bn_apex_radius_px.set(radius_px)
        self.bn_rotation.set(rotation)
        self.bn_residuals.set(residuals)
        self.bn_arclengths.set(arclengths)
        self.bn_drop_profile_fit.set(closest.T)

        self.bn_apex_radius.set(radius)
        self.bn_surface_area.set(surface_area)
        self.bn_volume.set(volume)
        self.bn_interfacial_tension.set(ift)
        self.bn_worthington.set(worthington)

        self.bn_status.set(self.Status.FINISHED)

    def cancel(self) -> None:
        if self.bn_status.get().is_terminal:
            # This is already at the end of its life.
            return

        if self.bn_status.get() is self.Status.WAITING_FOR_IMAGE:
            self._input_image.cancel()

        if self._extracted_features is not None:
            self._extracted_features.cancel()

        if self._young_laplace_fit is not None:
            self._young_laplace_fit.cancel()

        self.bn_status.set(self.Status.CANCELLED)

    def _get_status(self) -> Status:
        return self._status

    def _set_status(self, new_status: Status) -> None:
        self._status = new_status
        self.bn_is_cancelled.poke()

        if new_status.is_terminal:
            self._time_end = time.time()

    def _get_image(self) -> Optional[np.ndarray]:
        return self._image

    def _get_image_timestamp(self) -> float:
        return self._image_timestamp

    def _get_is_done(self) -> bool:
        return self.bn_status.get().is_terminal

    def _get_is_cancelled(self) -> bool:
        return self.bn_status.get() is self.Status.CANCELLED

    def _get_progress(self) -> float:
        if self.bn_is_done.get():
            return 1
        else:
            return 0

    def _get_time_start(self) -> float:
        return self._time_start

    def _get_time_est_complete(self) -> float:
        if self._input_image is None:
            return math.nan

        return self._input_image.est_ready

    def calculate_time_elapsed(self) -> float:
        time_start = self._time_start

        if math.isfinite(self._time_end):
            time_elapsed = self._time_end - time_start
        else:
            time_now = time.time()
            time_elapsed = time_now - time_start

        return time_elapsed

    def calculate_time_remaining(self) -> float:
        if self.bn_is_done.get():
            return 0

        time_est_complete = self.bn_time_est_complete.get()
        time_now = time.time()
        time_remaining = time_est_complete - time_now

        return time_remaining

    @property
    def is_image_replicated(self) -> bool:
        return self._input_image.is_replicated
