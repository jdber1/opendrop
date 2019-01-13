from opendrop.app.common.analysis_model.image_acquisition.image_acquisition import ImageAcquisition
from opendrop.app.ift.analysis_model.analyser import IFTAnalysis
from opendrop.app.ift.analysis_model.image_annotator.image_annotator import IFTImageAnnotator
from opendrop.app.ift.analysis_model.phys_params import IFTPhysicalParametersFactory


class IFTAnalysisFactory:
    def __init__(self, image_acquisition: ImageAcquisition, phys_params_factory: IFTPhysicalParametersFactory,
                 image_annotator: IFTImageAnnotator) -> None:
        self._image_acquisition = image_acquisition
        self._phys_params_factory = phys_params_factory
        self._image_annotator = image_annotator

    def create_analysis(self) -> IFTAnalysis:
        return IFTAnalysis(
            self._image_acquisition.acquire_images(),
            self._phys_params_factory.create_physical_parameters(),
            self._image_annotator.annotate_image)
