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
#E. Huang, T. Denning, A. Skoufis, J. Qi, R. R. Dagastine, R. F. Tabor
#and J. D. Berry, OpenDrop: Open-source software for pendant drop
#tensiometry & contact angle measurements, submitted to the Journal of
# Open Source Software
#
#These citations help us not only to understand who is using and
#developing OpenDrop, and for what purpose, but also to justify
#continued development of this code and other open source resources.
#
# OpenDrop is distributed WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.  You
# should have received a copy of the GNU General Public License along
# with this software.  If not, see <https://www.gnu.org/licenses/>.
import asyncio
import math
from typing import Optional, Tuple

import numpy as np

from opendrop.processing.ift import (
    apply_edge_detection,
    extract_drop_profile,
    extract_needle_profile,
    calculate_width_from_needle_profile,
)
from opendrop.utility.bindable import BoxBindable, AccessorBindable, thread_safe_bindable_collection, Bindable
from opendrop.utility.updaterworker import UpdaterWorker


class FeatureExtractorParams:
    def __init__(self) -> None:
        self.bn_needle_region_px = BoxBindable(None)
        self.bn_drop_region_px = BoxBindable(None)
        self.bn_canny_min = BoxBindable(30)
        self.bn_canny_max = BoxBindable(60)


class FeatureExtractor:
    _Data = thread_safe_bindable_collection(
        fields=[
            'bn_edge_detection',
            'bn_drop_profile_px',
            'bn_needle_profile_px',
            'bn_needle_width_px',
        ]
    )

    def __init__(self, image: Bindable[np.ndarray], params: 'FeatureExtractorParams', *,
                 loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
        self._loop = loop or asyncio.get_event_loop()

        self._bn_image = image

        self.params = params

        self._data = self._Data(
            _loop=self._loop,
            bn_edge_detection=None,
            bn_drop_profile_px=None,
            bn_needle_profile_px=None,
            bn_needle_width_px=math.nan,
        )

        self.is_busy = AccessorBindable(getter=self.get_is_busy)
        self._updater_worker = UpdaterWorker(
            do_update=self._update,
            on_idle=self.is_busy.poke,
            loop=self._loop,
        )

        self.bn_edge_detection = self._data.bn_edge_detection  # type: Bindable[Optional[np.ndarray]]
        self.bn_drop_profile_px = self._data.bn_drop_profile_px  # type: Bindable[Optional[np.ndarray]]
        self.bn_needle_profile_px = self._data.bn_needle_profile_px  # type: Bindable[Optional[Tuple[np.ndarray, np.ndarray]]]
        self.bn_needle_width_px = self._data.bn_needle_width_px  # type: Bindable[float]

        # Update extracted features whenever image or params change.
        self._bn_image.on_changed.connect(self._queue_update)
        self.params.bn_drop_region_px.on_changed.connect(self._queue_update)
        self.params.bn_needle_region_px.on_changed.connect(self._queue_update)
        self.params.bn_canny_min.on_changed.connect(self._queue_update)
        self.params.bn_canny_max.on_changed.connect(self._queue_update)

        # First update to initialise features.
        self._queue_update()

    def _queue_update(self) -> None:
        was_busy = self._updater_worker.is_busy
        self._updater_worker.queue_update()
        if not was_busy:
            self.is_busy.poke()

    # This method will be run on different threads (could be called by UpdaterWorker), so make sure it stays
    # thread-safe.
    def _update(self) -> None:
        editor = self._data.edit(timeout=1)
        assert editor is not None

        try:
            new_edge_detection = self._apply_edge_detection()
            new_drop_profile_px = self._extract_drop_profile_px(new_edge_detection)
            new_needle_profile_px = self._extract_needle_profile_px(new_edge_detection)
            new_needle_width_px = self._extract_needle_width_px(new_needle_profile_px)

            editor.set_value('bn_edge_detection', new_edge_detection)
            editor.set_value('bn_drop_profile_px', new_drop_profile_px)
            editor.set_value('bn_needle_profile_px', new_needle_profile_px)
            editor.set_value('bn_needle_width_px', new_needle_width_px)
        except Exception as exc:
            # If any exceptions occur, discard changes and re-raise the exception.
            editor.discard()
            raise exc
        else:
            # Otherwise commit the changes.
            editor.commit()

    def _apply_edge_detection(self) -> Optional[np.ndarray]:
        image = self._bn_image.get()
        if image is None:
            return None

        return apply_edge_detection(
            image=image,
            canny_min=self.params.bn_canny_min.get(),
            canny_max=self.params.bn_canny_max.get(),
        )

    def _extract_drop_profile_px(self, binary_image: Optional[np.ndarray]) -> Optional[np.ndarray]:
        if binary_image is None:
            return None

        drop_region = self.params.bn_drop_region_px.get()
        if drop_region is None:
            return None

        drop_region = drop_region.as_type(int)

        drop_image = binary_image[drop_region.y0:drop_region.y1, drop_region.x0:drop_region.x1]

        drop_profile_px = extract_drop_profile(drop_image)
        drop_profile_px += drop_region.pos

        return drop_profile_px

    def _extract_needle_profile_px(self, binary_image: Optional[np.ndarray]) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        if binary_image is None:
            return None

        needle_region = self.params.bn_needle_region_px.get()
        if needle_region is None:
            return None

        needle_region = needle_region.as_type(int)

        needle_image = binary_image[needle_region.y0:needle_region.y1, needle_region.x0:needle_region.x1]

        needle_profile_px = extract_needle_profile(needle_image)
        needle_profile_px = tuple(x + needle_region.pos for x in needle_profile_px)

        return needle_profile_px

    def _extract_needle_width_px(self, needle_profile: Optional[Tuple[np.ndarray, np.ndarray]]) -> float:
        if needle_profile is None:
            return math.nan

        return calculate_width_from_needle_profile(needle_profile)

    @property
    def is_sessile(self) -> bool:
        drop_region = self.params.bn_drop_region_px.get()
        needle_region = self.params.bn_needle_region_px.get()

        if needle_region is None or drop_region is None:
            # Can't determine if is sessile, just return False.
            return False

        if needle_region.p0.y > drop_region.p0.y:
            # Needle region is below drop region, probably sessile drop.
            return True

    def get_is_busy(self) -> bool:
        return self._updater_worker.is_busy

    async def wait_until_not_busy(self) -> None:
        while self.is_busy.get():
            await self.is_busy.on_changed.wait()
