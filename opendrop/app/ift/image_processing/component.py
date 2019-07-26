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
