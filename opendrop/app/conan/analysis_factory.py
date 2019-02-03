from opendrop.app.common.model.image_acquisition.image_acquisition import ImageAcquisition
from .model.analyser import ConanAnalysis
from .model.image_annotator.image_annotator import ConanImageAnnotator


class ConanAnalysisFactory:
    def __init__(self, image_acquisition: ImageAcquisition, image_annotator: ConanImageAnnotator) -> None:
        self._image_acquisition = image_acquisition
        self._image_annotator = image_annotator

    def create_analysis(self) -> ConanAnalysis:
        return ConanAnalysis(
            scheduled_images=self._image_acquisition.acquire_images(),
            annotate_image=self._image_annotator.annotate_image)
