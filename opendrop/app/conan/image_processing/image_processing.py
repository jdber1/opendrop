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


from gi.repository import Gtk
from injector import inject

from opendrop.app.common.image_processing.image_processor import image_processor_cs
from opendrop.appfw import Presenter, component

from .services.image_processing import ConanImageProcessingModel
from .services.plugins import ToolID
from .services.plugins.baseline import conan_baseline_plugin_cs
from .services.plugins.roi import conan_roi_plugin_cs
from .services.plugins.thresh import conan_thresh_plugin_cs
from .services.plugins.preview import conan_preview_plugin_cs


@component(
    template_path='./image_processing.ui',
)
class ConanImageProcessingPresenter(Presenter[Gtk.Container]):
    @inject
    def __init__(self, service: ConanImageProcessingModel) -> None:
        self.service = service

    def after_view_init(self) -> None:
        self.image_processor_component = image_processor_cs.factory(
            active_tool=self.service.bn_active_tool,
            tool_ids=[
                ToolID.BASELINE,
                ToolID.ROI,
                ToolID.THRESH,
            ],
            plugins=[
                conan_baseline_plugin_cs.factory(
                    model=self.service.baseline_plugin,
                    z_index=DrawPriority.OVERLAY,
                ),
                conan_roi_plugin_cs.factory(
                    model=self.service.roi_plugin,
                    z_index=DrawPriority.OVERLAY,
                ),
                conan_thresh_plugin_cs.factory(
                    model=self.service.thresh_plugin,
                ),
                conan_preview_plugin_cs.factory(
                    model=self.service.preview_plugin,
                    z_index=DrawPriority.BACKGROUND,
                ),
            ]
        ).create()
        self.image_processor_component.view_rep.show()
        self.host.add(self.image_processor_component.view_rep)

    def destroy(self, *_) -> None:
        self.image_processor_component.destroy()


class DrawPriority:
    BACKGROUND = 0
    OVERLAY = 1
