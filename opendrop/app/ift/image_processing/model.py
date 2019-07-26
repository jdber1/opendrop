from typing import Callable, Optional

import numpy as np

from opendrop.app.common.image_acquisition import ImageAcquisitionModel
from opendrop.app.common.image_processing.plugins.define_region import DefineRegionPluginModel
from opendrop.app.ift.analysis import FeatureExtractor, FeatureExtractorParams
from opendrop.utility.bindable import BoxBindable, Bindable, AccessorBindable
from opendrop.utility.geometry import Rect2
from .plugins import ToolID
from .plugins.edge_detection import EdgeDetectionPluginModel
from .plugins.preview import IFTPreviewPluginModel


class IFTImageProcessingModel:
    def __init__(
            self, *,
            image_acquisition: ImageAcquisitionModel,
            feature_extractor_params: FeatureExtractorParams,
            do_extract_features: Callable[[Bindable[np.ndarray], FeatureExtractorParams], FeatureExtractor]
    ) -> None:
        self._image_acquisition = image_acquisition
        self._feature_extractor_params = feature_extractor_params
        self._do_extract_features = do_extract_features

        self.bn_active_tool = BoxBindable(ToolID.DROP_REGION)

        region_clip = AccessorBindable(
            getter=self._get_region_clip
        )

        self.drop_region_plugin = DefineRegionPluginModel(
            in_region=self._feature_extractor_params.bn_drop_region_px,
            in_clip=region_clip,
        )

        self.needle_region_plugin = DefineRegionPluginModel(
            in_region=self._feature_extractor_params.bn_needle_region_px,
            in_clip=region_clip,
        )

        self.edge_detection_plugin = EdgeDetectionPluginModel(
            feature_extractor_params=feature_extractor_params,
        )

        self.preview_plugin = IFTPreviewPluginModel(
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
