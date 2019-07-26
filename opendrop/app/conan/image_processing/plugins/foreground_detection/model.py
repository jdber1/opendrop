from opendrop.app.conan.analysis import FeatureExtractorParams


class ForegroundDetectionPluginModel:
    def __init__(self, feature_extractor_params: FeatureExtractorParams) -> None:
        self._feature_extractor_params = feature_extractor_params

        self.bn_thresh = feature_extractor_params.bn_thresh
