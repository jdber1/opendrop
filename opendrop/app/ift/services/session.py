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

from gi.repository import GObject
from injector import Binder, Module, inject, singleton
import numpy as np

from opendrop.app.common.image_acquisition import AcquirerType, ImageAcquisitionModel
from opendrop.app.ift.analysis import IFTDropAnalysis, YoungLaplaceFitter
from opendrop.app.ift.analysis_saver import IFTAnalysisSaverOptions
from opendrop.app.ift.analysis_saver.save_functions import save_drops
from opendrop.utility.bindable.typing import Bindable

from .features import FeatureExtractor, FeatureExtractorParams, FeatureExtractorService
from .quantities import PhysicalPropertiesCalculator, PhysicalPropertiesCalculatorParams


class IFTSessionModule(Module):
    def configure(self, binder: Binder):
        binder.bind(ImageAcquisitionModel, to=ImageAcquisitionModel, scope=singleton)
        binder.bind(PhysicalPropertiesCalculatorParams, to=PhysicalPropertiesCalculatorParams, scope=singleton)
        binder.bind(FeatureExtractorParams, to=FeatureExtractorParams, scope=singleton)
        binder.bind(FeatureExtractorService, to=FeatureExtractorService, scope=singleton)

        binder.bind(IFTSession, to=IFTSession, scope=singleton)


class IFTSession(GObject.Object):
    @inject
    def __init__(
            self,
            image_acquisition: ImageAcquisitionModel,
            physprops_calculator_params: PhysicalPropertiesCalculatorParams,
            feature_extractor_params: FeatureExtractorParams,
    ) -> None:
        self._loop = asyncio.get_event_loop()

        self._analyses = ()
        self._analyses_saved = False

        self.image_acquisition = image_acquisition
        self.image_acquisition.use_acquirer_type(AcquirerType.LOCAL_STORAGE)
        self._physprops_calculator_params = physprops_calculator_params
        self._feature_extractor_params = feature_extractor_params

        super().__init__()

    @GObject.Property(flags=GObject.ParamFlags.READABLE | GObject.ParamFlags.EXPLICIT_NOTIFY)
    def analyses(self) -> Sequence[IFTDropAnalysis]:
        return self._analyses

    @GObject.Property(flags=GObject.ParamFlags.READABLE | GObject.ParamFlags.EXPLICIT_NOTIFY)
    def analyses_saved(self) -> bool:
        return self._analyses_saved

    def safe_to_discard(self) -> bool:
        if self._analyses_saved:
            return True

        if not self._analyses:
            return True

        all_images_replicated = all(
            analysis.is_image_replicated
            for analysis in self._analyses
        )
        if all_images_replicated:
            return True

        return False

    def start_analyses(self) -> None:
        assert not self._analyses

        input_images = self.image_acquisition.acquire_images()

        self._analyses = tuple(
            IFTDropAnalysis(
                input_image=im,
                do_extract_features=self.extract_features,
                do_young_laplace_fit=self.young_laplace_fit,
                do_calculate_physprops=self.calculate_physprops,
            ) for im in input_images
        )
        self._analyses_saved = False
        self.notify('analyses')
        self.notify('analyses_saved')

    def cancel_analyses(self) -> None:
        for analysis in self._analyses:
            analysis.cancel()

    def clear_analyses(self) -> None:
        self.cancel_analyses()
        self._analyses = ()
        self._analyses_saved = True
        self.notify('analyses')
        self.notify('analyses_saved')

    def save_analyses(self, options: IFTAnalysisSaverOptions) -> None:
        if not self._analyses: return
        save_drops(self._analyses, options)
        self._analyses_saved = True
        self.notify('analyses_saved')

    def create_save_options(self) -> IFTAnalysisSaverOptions:
        return IFTAnalysisSaverOptions()

    def extract_features(self, image: Bindable[np.ndarray]) -> FeatureExtractor:
        return FeatureExtractor(
            image=image,
            params=self._feature_extractor_params,
            loop=self._loop,
        )

    def young_laplace_fit(self, extracted_features: FeatureExtractor) -> YoungLaplaceFitter:
        return YoungLaplaceFitter(
            features=extracted_features,
            loop=self._loop
        )

    def calculate_physprops(
            self,
            extracted_features: FeatureExtractor,
            young_laplace_fit: YoungLaplaceFitter
    ) -> PhysicalPropertiesCalculator:
        return PhysicalPropertiesCalculator(
            features=extracted_features,
            young_laplace_fit=young_laplace_fit,
            params=self._physprops_calculator_params,
        )

    def quit(self) -> None:
        self.clear_analyses()
        self.image_acquisition.destroy()
