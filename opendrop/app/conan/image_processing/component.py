from gi.repository import Gtk

from opendrop.app.common.footer.linearnav import linear_navigator_footer_cs
from opendrop.app.common.image_processing.image_processor import image_processor_cs
from opendrop.app.common.wizard import WizardPageControls
from opendrop.app.conan.image_processing.plugins.surface import conan_surface_plugin_cs
from opendrop.mvp import ComponentSymbol, View, Presenter
from .model import ConanImageProcessingModel
from .plugins import ToolID
from .plugins.drop_region import conan_drop_region_plugin_cs
from .plugins.foreground_detection import foreground_detection_plugin_cs
from .plugins.preview import conan_preview_plugin_cs

conan_image_processing_cs = ComponentSymbol()  # type: ComponentSymbol[Gtk.Widget]


@conan_image_processing_cs.view(options=['footer_area'])
class ConanImageProcessingView(View['ConanImageProcessingPresenter', Gtk.Widget]):
    def _do_init(self, footer_area: Gtk.Widget) -> Gtk.Widget:
        self._widget = Gtk.Grid()

        _, image_processor_area = self.new_component(
            image_processor_cs.factory(
                active_tool=self.presenter.bn_active_tool,
                tool_ids=[
                    ToolID.DROP_REGION,
                    ToolID.SURFACE,
                    ToolID.FOREGROUND_DETECTION,
                ],
                plugins=[
                    conan_drop_region_plugin_cs.factory(
                        model=self.presenter.drop_region_plugin_model,
                        z_index=DrawPriority.OVERLAY,
                    ),
                    conan_surface_plugin_cs.factory(
                        model=self.presenter.surface_plugin_model,
                        z_index=DrawPriority.OVERLAY,
                    ),
                    foreground_detection_plugin_cs.factory(
                        model=self.presenter.foreground_detection_plugin_model,
                    ),
                    conan_preview_plugin_cs.factory(
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


@conan_image_processing_cs.presenter(options=['model', 'page_controls'])
class ConanImageProcessingPresenter(Presenter['ConanImageProcessingView']):
    def _do_init(self, model: ConanImageProcessingModel, page_controls: WizardPageControls) -> None:
        self._model = model
        self._page_controls = page_controls

        self.bn_active_tool = model.bn_active_tool

        self.drop_region_plugin_model = model.drop_region_plugin
        self.surface_plugin_model = model.surface_plugin
        self.foreground_detection_plugin_model = model.foreground_detection_plugin

        self.preview_plugin_model = model.preview_plugin

    def next_page(self) -> None:
        self._page_controls.next_page()

    def prev_page(self) -> None:
        self._page_controls.prev_page()
