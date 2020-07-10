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

from opendrop.app.common.image_processing.image_processor import image_processor_cs
from .services.image_processing import IFTImageProcessingModel
from .services.plugins import ToolID
from .services.plugins.drop_region import ift_drop_region_plugin_cs
from .services.plugins.edge_detection import edge_detection_plugin_cs
from .services.plugins.needle_region import ift_needle_region_plugin_cs
from .services.plugins.preview import ift_preview_plugin_cs

from opendrop.appfw import injection_container, Inject


class DrawPriority:
    BACKGROUND = 0
    OVERLAY = 1


@injection_container()
class IFTImageProcessing(Gtk.Grid):
    _service = Inject(IFTImageProcessingModel)

    def __init__(self, **properties) -> None:
        super().__init__(**properties)

        self._image_processor_component = image_processor_cs.factory(
            active_tool=self._service.bn_active_tool,
            tool_ids=[
                ToolID.DROP_REGION,
                ToolID.NEEDLE_REGION,
                ToolID.EDGE_DETECTION,
            ],
            plugins=[
                ift_drop_region_plugin_cs.factory(
                    model=self._service.drop_region_plugin,
                    z_index=DrawPriority.OVERLAY,
                ),
                ift_needle_region_plugin_cs.factory(
                    model=self._service.needle_region_plugin,
                    z_index=DrawPriority.OVERLAY,
                ),
                edge_detection_plugin_cs.factory(
                    model=self._service.edge_detection_plugin,
                ),
                ift_preview_plugin_cs.factory(
                    model=self._service.preview_plugin,
                    z_index=DrawPriority.BACKGROUND,
                ),
            ]
        ).create()
        self._image_processor_component.view_rep.show()
        self.add(self._image_processor_component.view_rep)

    def do_destroy(self) -> None:
        self._image_processor_component.destroy()
        Gtk.Grid.do_destroy.invoke(Gtk.Grid, self)
