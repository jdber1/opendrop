from collections import OrderedDict
from typing import Any, Iterable, Callable

from gi.repository import Gtk

from opendrop.mvp import View, Presenter, ComponentSymbol
from opendrop.mvp.typing import ComponentFactory
from opendrop.utility.bindable import Bindable
from opendrop.widgets.render import Render
from .tool_panel.component import tool_panel_cs, ToolItemRef

image_processor_cs = ComponentSymbol()  # type: ComponentSymbol[Gtk.Widget]


@image_processor_cs.view(options=['tool_ids', 'plugins'])
class ImageProcessorView(View['ImageProcessorPresenter', Gtk.Widget]):
    def _do_init(self, tool_ids: Iterable[Any], plugins: Iterable[ComponentFactory]) -> Gtk.Widget:
        self._widget = Gtk.Grid()

        self._render = Render(hexpand=True, vexpand=True)
        self._render.show()
        self._widget.attach(self._render, 0, 0, 1, 1)

        extras_area = Gtk.Grid(hexpand=True, vexpand=False, margin=5)
        extras_area.show()
        self._widget.attach(extras_area, 0, 1, 1, 1)

        self._tool_item_refs = OrderedDict(
            (tool_id, ToolItemRef())
            for tool_id in tool_ids
        )

        _, self._tool_panel_area = self.new_component(
            tool_panel_cs.factory(
                active_tool=self.presenter.bn_active_tool,
                do_activate_tool=self.presenter.activate_tool,
                tool_item_refs=self._tool_item_refs,
            )
        )

        for plugin in plugins:
            self.new_component(
                plugin.fork(
                    view_context=ImageProcessorPluginViewContext(
                        render=self._render,
                        extras_area=extras_area,
                        do_get_tool_item=self._get_tool_item,
                    )
                )
            )

        self._tool_panel_area.show()
        self._widget.attach(self._tool_panel_area, 0, 2, 1, 1)

        self._widget.show()

        return self._widget

    def _get_tool_item(self, tool_id: Any) -> ToolItemRef:
        return self._tool_item_refs[tool_id]

    def _do_destroy(self) -> None:
        self._widget.destroy()


class ImageProcessorPluginViewContext:
    def __init__(
            self,
            render: Render,
            extras_area: Gtk.Grid,
            do_get_tool_item: Callable[[Any], ToolItemRef]
    ) -> None:
        self.render = render
        self.extras_area = extras_area
        self._do_get_tool_item = do_get_tool_item

    def get_tool_item(self, tool_id: Any) -> ToolItemRef:
        return self._do_get_tool_item(tool_id)


@image_processor_cs.presenter(options=['active_tool'])
class ImageProcessorPresenter(Presenter['ImageProcessorView']):
    def _do_init(self, active_tool: Bindable[Any]) -> None:
        self.bn_active_tool = active_tool

    def activate_tool(self, tool_id: Any) -> None:
        self.bn_active_tool.set(tool_id)
