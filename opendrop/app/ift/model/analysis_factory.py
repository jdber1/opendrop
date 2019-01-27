from opendrop.app.common.model.image_acquisition.image_acquisition import ImageAcquisition
from opendrop.app.ift.model.analyser import IFTAnalysis
from opendrop.app.ift.model.image_annotator.image_annotator import IFTImageAnnotator
from opendrop.app.ift.model.phys_params import IFTPhysicalParametersFactory


class IFTAnalysisFactory:
    def __init__(self, image_acquisition: ImageAcquisition, phys_params_factory: IFTPhysicalParametersFactory,
                 image_annotator: IFTImageAnnotator) -> None:
        self._image_acquisition = image_acquisition
        self._phys_params_factory = phys_params_factory
        self._image_annotator = image_annotator

    def create_analysis(self) -> IFTAnalysis:
        return IFTAnalysis(
            scheduled_images=self._image_acquisition.acquire_images(),
            annotate_image=self._image_annotator.annotate_image,
            phys_params=self._phys_params_factory.create_physical_parameters())
