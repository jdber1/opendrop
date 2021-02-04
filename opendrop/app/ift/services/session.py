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


from typing import Sequence

from gi.repository import GObject
from injector import Binder, Module, inject, singleton

from opendrop.app.common.services.acquisition import AcquirerType, ImageAcquisitionService
from opendrop.app.ift.analysis_saver import IFTAnalysisSaverOptions
from opendrop.app.ift.analysis_saver.save_functions import save_drops

from .analysis import PendantAnalysisService, PendantAnalysisJob
from .edges import PendantEdgeDetectionService, PendantEdgeDetectionParamsFactory
from .quantities import PendantPhysicalParamsFactory
from .younglaplace import YoungLaplaceFitService


class IFTSessionModule(Module):
    def configure(self, binder: Binder):
        binder.bind(ImageAcquisitionService, to=ImageAcquisitionService, scope=singleton)

        binder.bind(PendantEdgeDetectionParamsFactory, scope=singleton)
        binder.bind(PendantPhysicalParamsFactory, scope=singleton)

        binder.bind(PendantEdgeDetectionService, scope=singleton)
        binder.bind(YoungLaplaceFitService, scope=singleton)

        binder.bind(PendantAnalysisService, scope=singleton)

        binder.bind(IFTSession, to=IFTSession, scope=singleton)


class IFTSession(GObject.Object):
    @inject
    def __init__(
            self,
            image_acquisition: ImageAcquisitionService,
            edge_det_service: PendantEdgeDetectionService,
            ylfit_service: YoungLaplaceFitService,
            analysis_service: PendantAnalysisService,
    ) -> None:
        self._analyses = ()
        self._analyses_saved = False

        self._image_acquisition = image_acquisition

        self._edge_det_service = edge_det_service
        self._ylfit_service = ylfit_service

        self._analysis_service = analysis_service

        super().__init__()

        self._image_acquisition.use_acquirer_type(AcquirerType.LOCAL_STORAGE)

    @GObject.Property(flags=GObject.ParamFlags.READABLE | GObject.ParamFlags.EXPLICIT_NOTIFY)
    def analyses(self) -> Sequence[PendantAnalysisJob]:
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

        input_images = self._image_acquisition.acquire_images()

        self._analyses = tuple(
            self._analysis_service.analyse(im) for im in input_images
        )
        self._analyses_saved = False
        self.notify('analyses')
        self.notify('analyses_saved')

    def cancel_analyses(self) -> None:
        keep_analyses = []
        for analysis in self._analyses:
            if analysis.bn_status.get() == PendantAnalysisJob.Status.WAITING_FOR_IMAGE:
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

    def save_analyses(self, options: IFTAnalysisSaverOptions) -> None:
        if not self._analyses: return
        save_drops(self._analyses, options)
        self._analyses_saved = True
        self.notify('analyses_saved')

    def create_save_options(self) -> IFTAnalysisSaverOptions:
        return IFTAnalysisSaverOptions()

    def quit(self) -> None:
        self.clear_analyses()
        self._image_acquisition.destroy()
