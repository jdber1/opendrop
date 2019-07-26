from typing import Callable, Optional

import numpy as np

from opendrop.app.common.image_acquisition import ImageAcquisitionModel
from opendrop.app.common.image_processing.plugins.define_line import DefineLinePluginModel
from opendrop.app.common.image_processing.plugins.define_region import DefineRegionPluginModel
from opendrop.app.conan.analysis import FeatureExtractor, FeatureExtractorParams, ContactAngleCalculatorParams
from opendrop.utility.bindable import BoxBindable, Bindable, AccessorBindable
from opendrop.utility.geometry import Rect2
from .plugins import ToolID
from .plugins.foreground_detection import ForegroundDetectionPluginModel
from .plugins.preview import ConanPreviewPluginModel


class ConanImageProcessingModel:
    def __init__(
            self, *,
            image_acquisition: ImageAcquisitionModel,
            feature_extractor_params: FeatureExtractorParams,
            conancalc_params: ContactAngleCalculatorParams,
            do_extract_features: Callable[[Bindable[np.ndarray], FeatureExtractorParams], FeatureExtractor]
    ) -> None:
        self._image_acquisition = image_acquisition
        self._feature_extractor_params = feature_extractor_params
        self._conancalc_params = conancalc_params
        self._do_extract_features = do_extract_features

        self.bn_active_tool = BoxBindable(ToolID.DROP_REGION)

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

    def _get_region_clip(self) -> Optional[Rect2]:
        image_size_hint = self._image_acquisition.get_image_size_hint()
        if image_size_hint is None:
            return None

        return Rect2(
            pos=(0, 0),
            size=image_size_hint,
        )
