import asyncio
from typing import Sequence, Callable, Any

import numpy as np

from opendrop.app.common.image_acquisition import ImageAcquisitionModel, AcquirerType
from opendrop.utility.bindable import Bindable, BoxBindable
from .analysis import FeatureExtractor, FeatureExtractorParams, ContactAngleCalculator, ContactAngleCalculatorParams, \
    ConanAnalysis
from .analysis_saver import ConanAnalysisSaverOptions
from .analysis_saver.save_functions import save_drops
from .image_processing import ConanImageProcessingModel
from .results import ConanResultsModel


class ConanSession:
    def __init__(self, do_exit: Callable[[], Any], *, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

        self._do_exit = do_exit

        self._feature_extractor_params = FeatureExtractorParams()
        self._conancalc_params = ContactAngleCalculatorParams()

        self._bn_analyses = BoxBindable(tuple())  # type: Bindable[Sequence[ConanAnalysis]]
        self._analyses_saved = False

        self.image_acquisition = ImageAcquisitionModel()
        self.image_acquisition.use_acquirer_type(AcquirerType.LOCAL_STORAGE)

        self.image_processing = ConanImageProcessingModel(
            image_acquisition=self.image_acquisition,
            feature_extractor_params=self._feature_extractor_params,
            conancalc_params=self._conancalc_params,
            do_extract_features=self.extract_features,
        )

        self.results = ConanResultsModel(
            in_analyses=self._bn_analyses,
            do_cancel_analyses=self.cancel_analyses,
            do_save_analyses=self.save_analyses,
            create_save_options=self._create_save_options,
            check_if_safe_to_discard=self.check_if_safe_to_discard_analyses,
        )

    def start_analyses(self) -> None:
        assert len(self._bn_analyses.get()) == 0

        new_analyses = []

        input_images = self.image_acquisition.acquire_images()
        for input_image in input_images:
            new_analysis = ConanAnalysis(
                input_image=input_image,
                do_extract_features=self.extract_features,
                do_calculate_conan=self.calculate_contact_angle,
            )

            new_analyses.append(new_analysis)

        self._bn_analyses.set(new_analyses)
        self._analyses_saved = False

    def cancel_analyses(self) -> None:
        analyses = self._bn_analyses.get()

        for analysis in analyses:
            analysis.cancel()

    def clear_analyses(self) -> None:
        self.cancel_analyses()
        self._bn_analyses.set(tuple())

    def save_analyses(self, options: ConanAnalysisSaverOptions) -> None:
        analyses = self._bn_analyses.get()
        if len(analyses) == 0:
            return

        save_drops(analyses, options)
        self._analyses_saved = True

    def _create_save_options(self) -> ConanAnalysisSaverOptions:
        return ConanAnalysisSaverOptions()

    def check_if_safe_to_discard_analyses(self) -> bool:
        if self._analyses_saved:
            return True
        else:
            analyses = self._bn_analyses.get()
            if len(analyses) == 0:
                return True

            all_images_replicated = all(
                analysis.is_image_replicated
                for analysis in analyses
            )

            if not all_images_replicated:
                return False

            return True

    def extract_features(self, image: Bindable[np.ndarray]) -> FeatureExtractor:
        return FeatureExtractor(
            image=image,
            params=self._feature_extractor_params,
            loop=self._loop,
        )

    def calculate_contact_angle(self, extracted_features: FeatureExtractor) -> ContactAngleCalculator:
        return ContactAngleCalculator(
            features=extracted_features,
            params=self._conancalc_params,
        )

    def exit(self) -> None:
        self.clear_analyses()
        self.image_acquisition.destroy()
        self._do_exit()
