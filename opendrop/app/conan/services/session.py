# Copyright © 2020, Joseph Berry, Rico Tabor (opendrop.dev@gmail.com)
# OpenDrop is released under the GNU GPL License. You are free to
# modify and distribute the code, but always under the same license
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


from typing import Sequence

from gi.repository import GObject
from injector import Binder, Module, inject, singleton

from opendrop.app.common.services.acquisition import (
    AcquirerType,
    ImageAcquisitionService,
)

from .params import ConanParamsFactory
from .features import ConanFeaturesService
from .conan import ConanFitService
from .analysis import ConanAnalysisJob, ConanAnalysisStatus, ConanAnalysisService
from .save import ConanSaveParamsFactory, ConanSaveService


READABLE        = GObject.ParamFlags.READABLE
EXPLICIT_NOTIFY = GObject.ParamFlags.EXPLICIT_NOTIFY


class ConanSessionModule(Module):
    def configure(self, binder: Binder):
        binder.bind(ConanParamsFactory, scope=singleton)
        binder.bind(ConanSaveParamsFactory, scope=singleton)

        binder.bind(ConanFeaturesService, scope=singleton)
        binder.bind(ConanFitService, scope=singleton)
        binder.bind(ConanSaveService, scope=singleton)

        binder.bind(ConanSession, scope=singleton)


class ConanSession(GObject.Object):
    @inject
    def __init__(
            self,
            image_acquisition: ImageAcquisitionService,
            features_service: ConanFeaturesService,
            cafit_service: ConanFitService,
            analysis_service: ConanAnalysisService,
            save_service: ConanSaveService,
    ) -> None:
        self._analyses = ()
        self._analyses_saved = False

        self._image_acquisition = image_acquisition
        self._image_acquisition.use_acquirer_type(AcquirerType.LOCAL_STORAGE)

        self._features_service = features_service
        self._cafit_service = cafit_service
        self._analysis_service = analysis_service
        self._save_service = save_service

        super().__init__()

    @GObject.Property(flags=READABLE | EXPLICIT_NOTIFY)
    def analyses(self) -> Sequence[ConanAnalysisJob]:
        return self._analyses

    @GObject.Property(flags=READABLE | EXPLICIT_NOTIFY)
    def analyses_saved(self) -> bool:
        return self._analyses_saved

    def safe_to_discard(self) -> bool:
        if self._analyses_saved:
            return True

        if not self._analyses:
            return True

        all_images_replicated = all(
            analysis.image_replicated
            for analysis in self._analyses
        )
        if all_images_replicated:
            return True

        return False

    def start_analyses(self) -> None:
        assert not self._analyses

        sources = self._image_acquisition.acquire_images()
        self._analyses = tuple(
            self._analysis_service.analyse(s)
            for s in sources
        )
        self._analyses_saved = False

        self.notify('analyses')
        self.notify('analyses_saved')

    def cancel_analyses(self) -> None:
        keep_analyses = []
        for analysis in self._analyses:
            if analysis.status == ConanAnalysisStatus.WAITING_FOR_IMAGE:
                # If job is still waiting for image, then delete it
                analysis.cancel()
            else:
                analysis.cancel()
                keep_analyses.append(analysis)

        self._analyses = tuple(keep_analyses)
        self.notify('analyses')

    def clear_analyses(self) -> None:
        self.cancel_analyses()
        self._analyses = ()
        self._analyses_saved = True
        self.notify('analyses')
        self.notify('analyses_saved')

    def save_analyses(self) -> None:
        if not self._analyses: return
        self._save_service.save(self._analyses)
        self._analyses_saved = True
        self.notify('analyses_saved')

    def quit(self) -> None:
        self.clear_analyses()
        self._image_acquisition.destroy()
        self._features_service.destroy()
        self._cafit_service.destroy()
