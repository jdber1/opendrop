from gi.repository import Gtk

from opendrop.app.common.image_processing.image_processor import ImageProcessorPluginViewContext
from opendrop.app.common.image_processing.plugins.define_region import define_region_plugin_cs, DefineRegionPluginModel
from opendrop.app.ift.image_processing.plugins import ToolID
from opendrop.mvp import ComponentSymbol, View, Presenter

ift_needle_region_plugin_cs = ComponentSymbol()  # type: ComponentSymbol[None]


@ift_needle_region_plugin_cs.view(options=['view_context', 'z_index'])
class IFTNeedleRegionPluginView(View['IFTNeedleRegionPluginPresenter', None]):
    def _do_init(self, view_context: ImageProcessorPluginViewContext, z_index: int) -> None:
        self._view_context = view_context

        self.new_component(
            define_region_plugin_cs.factory(
                model=self.presenter.define_region_plugin_model,
                view_context=view_context,
                tool_id=ToolID.NEEDLE_REGION,
                color=(0.05, 0.1, 1.0),
                label='Needle region',
                z_index=z_index,
            ),
        )

        tool_ref = view_context.get_tool_item(ToolID.NEEDLE_REGION)
        self._tool_button_interior = Gtk.Grid(hexpand=True, vexpand=True)
        tool_ref.button_interior.add(self._tool_button_interior)

        tool_button_lbl = Gtk.Label(
            label='Needle region',
            vexpand=True,
            valign=Gtk.Align.CENTER,
        )
        self._tool_button_interior.add(tool_button_lbl)

        self._tool_button_interior.show_all()

    def _do_destroy(self) -> None:
        self._tool_button_interior.destroy()


@ift_needle_region_plugin_cs.presenter(options=['model'])
class IFTNeedleRegionPluginPresenter(Presenter['IFTNeedleRegionPluginView']):
    def _do_init(self, model: DefineRegionPluginModel) -> None:
        self.define_region_plugin_model = model
