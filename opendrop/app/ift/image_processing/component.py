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

from opendrop.app.common.footer.linearnav import linear_navigator_footer_cs
from opendrop.app.common.image_processing.image_processor import image_processor_cs
from opendrop.app.common.wizard import WizardPageControls
from opendrop.mvp import ComponentSymbol, View, Presenter
from .model import IFTImageProcessingModel
from .plugins import ToolID
from .plugins.drop_region import ift_drop_region_plugin_cs
from .plugins.edge_detection import edge_detection_plugin_cs
from .plugins.needle_region import ift_needle_region_plugin_cs
from .plugins.preview import ift_preview_plugin_cs

ift_image_processing_cs = ComponentSymbol()  # type: ComponentSymbol[Gtk.Widget]


@ift_image_processing_cs.view(options=['footer_area'])
class IFTImageProcessingView(View['IFTImageProcessingPresenter', Gtk.Widget]):
    def _do_init(self, footer_area: Gtk.Widget) -> Gtk.Widget:
        self._widget = Gtk.Grid()

        _, image_processor_area = self.new_component(
            image_processor_cs.factory(
                active_tool=self.presenter.bn_active_tool,
                tool_ids=[
                    ToolID.DROP_REGION,
                    ToolID.NEEDLE_REGION,
                    ToolID.EDGE_DETECTION,
                ],
                plugins=[
                    ift_drop_region_plugin_cs.factory(
                        model=self.presenter.drop_region_plugin_model,
                        z_index=DrawPriority.OVERLAY,
                    ),
                    ift_needle_region_plugin_cs.factory(
                        model=self.presenter.needle_region_plugin_model,
                        z_index=DrawPriority.OVERLAY,
                    ),
                    edge_detection_plugin_cs.factory(
                        model=self.presenter.edge_detection_plugin_model,
                    ),
                    ift_preview_plugin_cs.factory(
                        model=self.presenter.preview_plugin_model,
                        z_index=DrawPriority.BACKGROUND,
                    ),
                ]
            )
        )
        image_processor_area.show()

        self._widget.add(image_processor_area)
        self._widget.show()

        _, footer_inside = self.new_component(
            linear_navigator_footer_cs.factory(
                do_back=self.presenter.prev_page,
                do_next=self.presenter.next_page,
                next_label='Start analysis',
            )
        )
        footer_inside.show()
        footer_area.add(footer_inside)

        return self._widget

    def _do_destroy(self) -> None:
        self._widget.destroy()


class DrawPriority:
    BACKGROUND = 0
    OVERLAY = 1


@ift_image_processing_cs.presenter(options=['model', 'page_controls'])
class IFTImageProcessingPresenter(Presenter['IFTImageProcessingView']):
    def _do_init(self, model: IFTImageProcessingModel, page_controls: WizardPageControls) -> None:
        self._model = model
        self._page_controls = page_controls

        self.bn_active_tool = model.bn_active_tool

        self.drop_region_plugin_model = model.drop_region_plugin
        self.needle_region_plugin_model = model.needle_region_plugin
        self.edge_detection_plugin_model = model.edge_detection_plugin

        self.preview_plugin_model = model.preview_plugin

    def next_page(self) -> None:
        self._page_controls.next_page()

    def prev_page(self) -> None:
        self._page_controls.prev_page()
