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
from typing import Callable, Optional

import numpy as np

from opendrop.app.common.image_acquirer import InputImage
from opendrop.utility.bindable import AccessorBindable, VariableBindable
from opendrop.utility.bindable.typing import Bindable
from opendrop.utility.geometry import Vector2
from .features import FeatureExtractor
from .young_laplace_fit import YoungLaplaceFitter
from opendrop.app.ift.services.quantities import PhysicalPropertiesCalculator


# Classes

class IFTDropAnalysis:
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
            do_extract_features: Callable[[Bindable[np.ndarray]], FeatureExtractor],
            do_young_laplace_fit: Callable[[FeatureExtractor], YoungLaplaceFitter],
            do_calculate_physprops: Callable[[FeatureExtractor, YoungLaplaceFitter], PhysicalPropertiesCalculator]
    ) -> None:
        self._loop = asyncio.get_event_loop()

        self._time_start = time.time()
        self._time_end = math.nan

        self._input_image = input_image
        self._do_extract_features = do_extract_features
        self._do_young_laplace_fit = do_young_laplace_fit
        self._do_calculate_physprops = do_calculate_physprops

        self._status = self.Status.WAITING_FOR_IMAGE
        self.bn_status = AccessorBindable(
            getter=self._get_status,
            setter=self._set_status,
        )

        self._image = None  # type: Optional[np.ndarray]
        # The time (in Unix time) that the image was captured.
        self._image_timestamp = math.nan  # type: float

        self._extracted_features = None  # type: Optional[FeatureExtractor]
        self._physical_properties = None  # type: Optional[PhysicalPropertiesCalculator]
        self._young_laplace_fit = None  # type: Optional[YoungLaplaceFitter]

        self.bn_image = AccessorBindable(self._get_image)
        self.bn_image_timestamp = AccessorBindable(self._get_image_timestamp)

        # Attributes from YoungLaplaceFitter
        self.bn_bond_number = VariableBindable(math.nan)
        self.bn_apex_coords_px = VariableBindable(Vector2(math.nan, math.nan))
        self.bn_apex_radius_px = VariableBindable(math.nan)
        self.bn_rotation = VariableBindable(math.nan)
        self.bn_drop_profile_fit = VariableBindable(None)
        self.bn_residuals = VariableBindable(None)

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

        # Log
        self.bn_log = VariableBindable('')

        self.bn_is_done = AccessorBindable(getter=self._get_is_done)
        self.bn_is_cancelled = AccessorBindable(getter=self._get_is_cancelled)
        self.bn_progress = AccessorBindable(self._get_progress)
        self.bn_time_start = AccessorBindable(self._get_time_start)
        self.bn_time_est_complete = AccessorBindable(self._get_time_est_complete)

        self.bn_status.on_changed.connect(self.bn_is_done.poke)
        self.bn_status.on_changed.connect(self.bn_progress.poke)

        self._loop.create_task(self._input_image.read()).add_done_callback(self._hdl_input_image_read)

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

        extracted_features = self._do_extract_features(VariableBindable(self._image))
        young_laplace_fit = self._do_young_laplace_fit(extracted_features)
        physical_properties = self._do_calculate_physprops(extracted_features, young_laplace_fit)

        self._extracted_features = extracted_features
        self._young_laplace_fit = young_laplace_fit
        self._physical_properties = physical_properties

        self._bind_fit()

        self.bn_image.poke()
        self.bn_image_timestamp.poke()

        young_laplace_fit.bn_is_busy.on_changed.connect(
            self._hdl_young_laplace_fit_is_busy_changed
        )

        self.bn_status.set(self.Status.FITTING)

    def _bind_fit(self) -> None:
        # Bind extracted features attributes
        self._extracted_features.bn_drop_profile_px.bind_to(
            self.bn_drop_profile_extract
        )
        self._extracted_features.bn_needle_profile_px.bind_to(
            self.bn_needle_profile_extract
        )
        self._extracted_features.bn_needle_width_px.bind_to(
            self.bn_needle_width_px
        )
        self._extracted_features.params.bn_drop_region_px.bind_to(
            self.bn_drop_region
        )
        self._extracted_features.params.bn_needle_region_px.bind_to(
            self.bn_needle_region
        )

        # Bind Young-Laplace fit attributes
        self._young_laplace_fit.bn_bond_number.bind_to(
            self.bn_bond_number
        )
        self._young_laplace_fit.bn_apex_pos.bind_to(
            self.bn_apex_coords_px
        )
        self._young_laplace_fit.bn_apex_radius.bind_to(
            self.bn_apex_radius_px
        )
        self._young_laplace_fit.bn_rotation.bind_to(
            self.bn_rotation
        )
        self._young_laplace_fit.bn_profile_fit.bind_to(
            self.bn_drop_profile_fit
        )
        self._young_laplace_fit.bn_residuals.bind_to(
            self.bn_residuals
        )
        self._young_laplace_fit.bn_log.bind_to(
            self.bn_log
        )

        # Bind physical properties attributes
        self._physical_properties.bn_interfacial_tension.bind_to(
            self.bn_interfacial_tension
        )
        self._physical_properties.bn_volume.bind_to(
            self.bn_volume
        )
        self._physical_properties.bn_surface_area.bind_to(
            self.bn_surface_area
        )
        self._physical_properties.bn_apex_radius.bind_to(
            self.bn_apex_radius
        )
        self._physical_properties.bn_worthington.bind_to(
            self.bn_worthington
        )

    def _hdl_young_laplace_fit_is_busy_changed(self) -> None:
        if self.bn_status.get() is self.Status.CANCELLED:
            return

        young_laplace_fit = self._young_laplace_fit

        # If bond number is a sensible value, then assume young_laplace_fit has completed.
        if not math.isnan(young_laplace_fit.bn_bond_number.get()):
            self.bn_status.set(self.Status.FINISHED)

    def cancel(self) -> None:
        if self.bn_status.get().is_terminal:
            # This is already at the end of its life.
            return

        if self.bn_status.get() is self.Status.WAITING_FOR_IMAGE:
            self._input_image.cancel()

        if self._young_laplace_fit is not None:
            self._young_laplace_fit.stop()

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
