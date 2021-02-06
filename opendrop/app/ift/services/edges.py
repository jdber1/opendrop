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
from concurrent.futures.process import ProcessPoolExecutor

from injector import inject
from opendrop.geometry import Rect2
from typing import Optional

from gi.repository import GObject

import numpy as np

from opendrop.processing.ift import (
    apply_edge_detection,
    extract_drop_profile,
    extract_needle_profile,
)


def pendant_edge_detect(image: np.ndarray, params: 'PendantEdgeDetectionParams') -> 'PendantEdgeDetection':
    edge_map = apply_edge_detection(image, canny_min=params.canny_min, canny_max=params.canny_max)

    drop_region = params.drop_region
    if drop_region is not None:
        cropped = edge_map[drop_region.y0:drop_region.y1, drop_region.x0:drop_region.x1]
        drop_edge = extract_drop_profile(cropped)
        drop_edge += drop_region.position
    else:
        drop_edge = np.empty((0, 2))

    needle_region = params.needle_region
    if needle_region is not None:
        cropped = edge_map[needle_region.y0:needle_region.y1, needle_region.x0:needle_region.x1]
        needle_edges = extract_needle_profile(cropped)
        needle_edges = tuple(s + needle_region.position for s in needle_edges)
    else:
        needle_edges = np.empty((0, 2)), np.empty((0, 2))

    return PendantEdgeDetection(
        edge_map=edge_map,
        drop_edge=drop_edge,
        needle_left_edge=needle_edges[0],
        needle_right_edge=needle_edges[1],
    )


class PendantEdgeDetectionParamsFactory(GObject.Object):
    _canny_min: int = 30
    _canny_max: int = 60
    _needle_region: Optional[Rect2[int]] = None
    _drop_region: Optional[Rect2[int]] = None

    def create(self) -> 'PendantEdgeDetectionParams':
        return PendantEdgeDetectionParams(
            canny_min=self._canny_min,
            canny_max=self._canny_max,
            needle_region=self._needle_region,
            drop_region=self._drop_region,
        )

    @GObject.Signal
    def changed(self) -> None:
        """Emitted when edge detection parameters are changed."""

    @GObject.Property
    def needle_region(self) -> Optional[Rect2[int]]:
        return self._needle_region

    @needle_region.setter
    def needle_region(self, region: Optional[Rect2[int]]) -> None:
        self._needle_region = region
        self.changed.emit()

    @GObject.Property
    def drop_region(self) -> Optional[Rect2[int]]:
        return self._drop_region

    @drop_region.setter
    def drop_region(self, region: Optional[Rect2[int]]) -> None:
        self._drop_region = region
        self.changed.emit()

    @GObject.Property
    def canny_min(self) -> int:
        return self._canny_min

    @canny_min.setter
    def canny_min(self, value: int) -> None:
        self._canny_min = value
        self.changed.emit()

    @GObject.Property
    def canny_max(self) -> int:
        return self._canny_max

    @canny_max.setter
    def canny_max(self, value: int) -> None:
        self._canny_max = value
        self.changed.emit()


class PendantEdgeDetectionParams:
    """Plain Old Data structure"""

    canny_min: int
    canny_max: int
    needle_region: Optional[Rect2[int]]
    drop_region: Optional[Rect2[int]]

    def __init__(
            self,
            canny_min: int,
            canny_max: int,
            needle_region: Optional[Rect2[int]],
            drop_region: Optional[Rect2[int]],
    ) -> None:
        self.canny_min = canny_min
        self.canny_max = canny_max
        self.needle_region = needle_region
        self.drop_region = drop_region


class PendantEdgeDetectionService:
    @inject
    def __init__(self, default_params_factory: PendantEdgeDetectionParamsFactory) -> None:
        self._executor = ProcessPoolExecutor()
        self._default_params_factory = default_params_factory

    def detect(self, image: np.ndarray, params: Optional[PendantEdgeDetectionParams] = None) -> asyncio.Future:
        if params is None:
            params = self._default_params_factory.create()

        cfut = self._executor.submit(pendant_edge_detect, image, params)
        fut = asyncio.wrap_future(cfut, loop=asyncio.get_event_loop())
        return fut

    def destroy(self) -> None:
        self._executor.shutdown()


class PendantEdgeDetection:
    edge_map: np.ndarray
    drop_edge: np.ndarray
    needle_left_edge: np.ndarray
    needle_right_edge: np.ndarray

    def __init__(
            self,
            edge_map: np.ndarray,
            drop_edge: np.ndarray,
            needle_left_edge: np.ndarray,
            needle_right_edge: np.ndarray,
    ) -> None:
        self.edge_map = edge_map
        self.drop_edge = drop_edge
        self.needle_left_edge = needle_left_edge
        self.needle_right_edge = needle_right_edge
