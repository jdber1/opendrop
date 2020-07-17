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


from typing import Callable, Optional

import numpy as np

from opendrop.app.common.services.acquisition import ImageAcquisitionService
from opendrop.app.common.image_processing.plugins.define_line import DefineLinePluginModel
from opendrop.app.common.image_processing.plugins.define_region import DefineRegionPluginModel
from opendrop.app.conan.analysis import FeatureExtractor, FeatureExtractorParams, ContactAngleCalculatorParams
from opendrop.utility.bindable import VariableBindable, AccessorBindable
from opendrop.utility.bindable.typing import Bindable
from opendrop.utility.geometry import Rect2
from .plugins import ToolID
from .plugins.foreground_detection import ForegroundDetectionPluginModel
from .plugins.preview import ConanPreviewPluginModel


class ConanImageProcessingModel:
    def __init__(
            self, *,
            image_acquisition: ImageAcquisitionService,
            feature_extractor_params: FeatureExtractorParams,
            conancalc_params: ContactAngleCalculatorParams,
            do_extract_features: Callable[[Bindable[np.ndarray], FeatureExtractorParams], FeatureExtractor]
    ) -> None:
        self._image_acquisition = image_acquisition
        self._feature_extractor_params = feature_extractor_params
        self._conancalc_params = conancalc_params
        self._do_extract_features = do_extract_features

        self.bn_active_tool = VariableBindable(ToolID.DROP_REGION)

        region_clip = AccessorBindable(
            getter=self._get_region_clip
        )

        self.drop_region_plugin = DefineRegionPluginModel(
            in_region=self._feature_extractor_params.bn_drop_region_px,
            in_clip=region_clip,
        )

        self.surface_plugin = DefineLinePluginModel(
            in_line=self._conancalc_params.bn_surface_line_px,
            in_clip=region_clip,
        )

        self.foreground_detection_plugin = ForegroundDetectionPluginModel(
            feature_extractor_params=feature_extractor_params,
        )

        self.preview_plugin = ConanPreviewPluginModel(
            image_acquisition=image_acquisition,
            feature_extractor_params=feature_extractor_params,
            do_extract_features=do_extract_features,
        )

    def _get_region_clip(self) -> Optional[Rect2[int]]:
        image_size_hint = self._image_acquisition.get_image_size_hint()
        if image_size_hint is None:
            return None

        return Rect2(
            position=(0, 0),
            size=image_size_hint,
        )
