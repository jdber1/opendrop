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
import threading
from typing import Optional

import numpy as np

from opendrop.app.ift.services.features import FeatureExtractor
from opendrop.processing.ift import YoungLaplaceFit
from opendrop.utility.bindable import thread_safe_bindable_collection, AccessorBindable
from opendrop.utility.bindable.typing import Bindable
from opendrop.utility.geometry import Vector2
from opendrop.utility.updaterworker import UpdaterWorker


class YoungLaplaceFitter:
    PROFILE_FIT_SAMPLES = 500

    _Data = thread_safe_bindable_collection(
        fields=[
            'apex_pos',
            'apex_radius',
            'bond_number',
            'rotation',
            'profile_fit',
            'residuals',
            'volume',
            'surface_area',
        ]
    )

    def __init__(self, features: FeatureExtractor, *,
                 loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
        self._loop = loop or asyncio.get_event_loop()

        self._features = features
        self._is_sessile = False

        self._data = self._Data(
            _loop=self._loop,
            apex_pos=Vector2(math.nan, math.nan),
            apex_radius=math.nan,
            bond_number=math.nan,
            rotation=math.nan,
            profile_fit=None,
            residuals=None,
            volume=math.nan,
            surface_area=math.nan,
        )

        self._stop_flag = False

        self.bn_is_busy = AccessorBindable(getter=self.get_is_busy)
        self._updater_worker = UpdaterWorker(
            do_update=self._update,
            on_idle=self.bn_is_busy.poke,
            loop=self._loop
        )

        self.bn_apex_pos = self._data.apex_pos  # type: Bindable[Vector2[float]]
        self.bn_apex_radius = self._data.apex_radius  # type: Bindable[float]
        self.bn_bond_number = self._data.bond_number  # type: Bindable[float]
        self.bn_rotation = self._data.rotation  # type: Bindable[float]
        self.bn_profile_fit = self._data.profile_fit  # type: Bindable[np.ndarray]
        self.bn_residuals = self._data.residuals  # type: Bindable[np.ndarray]
        self.bn_volume = self._data.volume  # type: Bindable[float]
        self.bn_surface_area = self._data.surface_area  # type: Bindable[float]

        self._log = ''
        self._log_lock = threading.Lock()
        self.bn_log = AccessorBindable(getter=self.get_log)

        # Reanalyse when extracted drop profile changes
        features.bn_drop_profile_px.on_changed.connect(
            self._hdl_features_changed
        )

        # First update to initialise attributes.
        self._queue_update()

    def _hdl_features_changed(self) -> None:
        self._queue_update()

    def _queue_update(self) -> None:
        was_busy = self._updater_worker.is_busy
        self._updater_worker.queue_update()

        if not was_busy:
            self.bn_is_busy.poke()

    # This method will be run on different threads (could be called by UpdaterWorker), so make sure it stays
    # thread-safe.
    def _update(self) -> None:
        if self._stop_flag:
            return

        drop_profile_px = self._features.bn_drop_profile_px.get()
        if drop_profile_px is None:
            return

        drop_profile_px = drop_profile_px.copy()

        self._is_sessile = self._features.is_sessile
        if not self._is_sessile:
            # YoungLaplaceFit takes in a drop profile where the drop is deformed in the negative y-direction.
            # (Remember that in 'image coordinates', positive y-direction is 'downwards')
            drop_profile_px[:, 1] *= -1

        self._clear_log()

        fit = YoungLaplaceFit(
            drop_profile=drop_profile_px,
            on_update=self._ylfit_incremental_update,
            logger=self._append_log
        )

    # This method will be run on different threads (could be called by UpdaterWorker), so make sure it stays
    # thread-safe.
    def _ylfit_incremental_update(self, ylfit: YoungLaplaceFit) -> None:
        if self._stop_flag:
            ylfit.cancel()
            return

        editor = self._data.edit(timeout=1)
        assert editor is not None

        try:
            apex_pos = Vector2(ylfit.apex_x, ylfit.apex_y)
            rotation = ylfit.rotation
            profile_fit = ylfit(np.linspace(0, 1, num=self.PROFILE_FIT_SAMPLES))

            if not self._is_sessile:
                apex_pos = Vector2(apex_pos.x, -apex_pos.y)
                rotation *= -1
                profile_fit[:, 1] *= -1

            editor.set_value('apex_pos', apex_pos)
            editor.set_value('apex_radius', ylfit.apex_radius)
            editor.set_value('bond_number', ylfit.bond_number)
            editor.set_value('rotation', rotation)
            editor.set_value('profile_fit', profile_fit)
            editor.set_value('residuals', ylfit.residuals)
            editor.set_value('volume', ylfit.volume)
            editor.set_value('surface_area', ylfit.surface_area)
        except Exception as exc:
            # If any exceptions occur, discard changes and re-raise the exception.
            editor.discard()
            raise exc
        else:
            # Otherwise commit the changes.
            editor.commit()

    def stop(self) -> None:
        self._stop_flag = True

    def get_is_busy(self) -> bool:
        return self._updater_worker.is_busy

    async def wait_until_not_busy(self) -> None:
        while self.bn_is_busy.get():
            await self.bn_is_busy.on_changed.wait()

    def _append_log(self, message: str) -> None:
        if message == '': return

        with self._log_lock:
            self._log += message

        self._loop.call_soon_threadsafe(self.bn_log.poke)

    def _clear_log(self) -> None:
        if self._log == '': return

        with self._log_lock:
            self._log = ''

        self._loop.call_soon_threadsafe(self.bn_log.poke)

    def get_log(self) -> str:
        with self._log_lock:
            return self._log
