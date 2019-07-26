from opendrop.app.ift.analysis import FeatureExtractorParams


class EdgeDetectionPluginModel:
    def __init__(self, feature_extractor_params: FeatureExtractorParams) -> None:
        self._feature_extractor_params = feature_extractor_params

        self.bn_canny_min = feature_extractor_params.bn_canny_min
        self.bn_canny_max = feature_extractor_params.bn_canny_max
