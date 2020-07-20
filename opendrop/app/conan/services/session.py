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
from typing import Sequence

from injector import Binder, Module, inject, singleton
import numpy as np

from opendrop.app.common.services.acquisition import AcquirerType, ImageAcquisitionService
from opendrop.app.conan.analysis import (
    ConanAnalysis,
    ContactAngleCalculator,
    ContactAngleCalculatorParams,
    FeatureExtractor,
    FeatureExtractorParams,
)
from opendrop.app.conan.analysis_saver import ConanAnalysisSaverOptions
from opendrop.app.conan.analysis_saver.save_functions import save_drops
from opendrop.app.conan.results import ConanResultsModel
from opendrop.utility.bindable import VariableBindable
from opendrop.utility.bindable.typing import Bindable


class ConanSessionModule(Module):
    def configure(self, binder: Binder):
        binder.bind(ImageAcquisitionService, to=ImageAcquisitionService, scope=singleton)
        binder.bind(FeatureExtractorParams, to=FeatureExtractorParams, scope=singleton)
        binder.bind(ContactAngleCalculatorParams, to=ContactAngleCalculatorParams, scope=singleton)

        binder.bind(ConanSession, to=ConanSession, scope=singleton)


class ConanSession:
    @inject
    def __init__(
            self,
            image_acquisition: ImageAcquisitionService,
            feature_extractor_params: FeatureExtractorParams,
            conancalc_params: ContactAngleCalculatorParams,
    ) -> None:
        self._feature_extractor_params = feature_extractor_params
        self._conancalc_params = conancalc_params

        self._bn_analyses = VariableBindable(tuple())  # type: Bindable[Sequence[ConanAnalysis]]
        self._analyses_saved = False

        self.image_acquisition = image_acquisition
        self.image_acquisition.use_acquirer_type(AcquirerType.LOCAL_STORAGE)

        self.results = ConanResultsModel(
            in_analyses=self._bn_analyses,
            do_cancel_analyses=self.cancel_analyses,
            do_save_analyses=self.save_analyses,
            create_save_options=self._create_save_options,
            check_if_safe_to_discard=self.safe_to_discard,
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

    def safe_to_discard(self) -> bool:
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
            loop=asyncio.get_event_loop(),
        )

    def calculate_contact_angle(self, extracted_features: FeatureExtractor) -> ContactAngleCalculator:
        return ContactAngleCalculator(
            features=extracted_features,
            params=self._conancalc_params,
        )

    def quit(self) -> None:
        self.clear_analyses()
        self.image_acquisition.destroy()
