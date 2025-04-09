# Copyright © 2020, Joseph Berry, Rico Tabor (opendrop.dev@gmail.com)
# OpenDrop is released under the GNU GPL License. You are free to
# modify and distribute the code, but always under the same license
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
from concurrent.futures.process import ProcessPoolExecutor
from injector import inject
from typing import Optional

from gi.repository import GObject
import numpy as np

from opendrop.geometry import Rect2
from opendrop.features.pendant import PendantFeatures, extract_pendant_features


__all__ = (
    'PendantFeaturesParams',
    'PendantFeatures',
    'PendantFeaturesParamsFactory',
    'PendantFeaturesService',
)


class PendantFeaturesParamsFactory(GObject.Object):
    _drop_region: Optional[Rect2[int]] = None
    _needle_region: Optional[Rect2[int]] = None
    _thresh1 = 80.0
    _thresh2 = 160.0

    def create(self) -> 'PendantFeaturesParams':
        return PendantFeaturesParams(
            drop_region=self._drop_region,
            needle_region=self._needle_region,
            thresh1=self._thresh1,
            thresh2=self._thresh2,
        )

    @GObject.Signal
    def changed(self) -> None:
        """Emitted when edge detection parameters are changed."""

    @GObject.Property
    def thresh1(self) -> float:
        return self._thresh1

    @thresh1.setter
    def thresh1(self, value: float) -> None:
        self._thresh1 = value
        self.changed.emit()

    @GObject.Property
    def thresh2(self) -> float:
        return self._thresh2

    @thresh2.setter
    def thresh2(self, value: float) -> None:
        self._thresh2 = value
        self.changed.emit()

    @GObject.Property
    def drop_region(self) -> Optional[Rect2[int]]:
        return self._drop_region

    @drop_region.setter
    def drop_region(self, region: Optional[Rect2[int]]) -> None:
        self._drop_region = region
        self.changed.emit()

    @GObject.Property
    def needle_region(self) -> Optional[Rect2[int]]:
        return self._needle_region

    @needle_region.setter
    def needle_region(self, region: Optional[Rect2[int]]) -> None:
        self._needle_region = region
        self.changed.emit()


class PendantFeaturesParams:
    """Plain Old Data structure"""

    thresh1: float
    thresh2: float
    needle_region: Optional[Rect2[int]]
    drop_region: Optional[Rect2[int]]

    def __init__(
            self,
            thresh1: float,
            thresh2: float,
            needle_region: Optional[Rect2[int]],
            drop_region: Optional[Rect2[int]],
    ) -> None:
        self.thresh1 = thresh1
        self.thresh2 = thresh2
        self.needle_region = needle_region
        self.drop_region = drop_region


class PendantFeaturesService:
    @inject
    def __init__(self, default_params_factory: PendantFeaturesParamsFactory) -> None:
        self._executor = ProcessPoolExecutor(max_workers=1)
        self._default_params_factory = default_params_factory

    def extract(
            self,
            image: np.ndarray,
            params: Optional[PendantFeaturesParams] = None,
            *,
            labels: bool = False,
    ) -> asyncio.Future:
        if params is None:
            params = self._default_params_factory.create()

        cfut = self._executor.submit(
            extract_pendant_features,
            image,
            params.drop_region,
            params.needle_region,
            thresh1=params.thresh1,
            thresh2=params.thresh2,
            labels=labels,
        )

        fut = asyncio.wrap_future(cfut, loop=asyncio.get_event_loop())
        return fut

    def destroy(self) -> None:
        self._executor.shutdown()
