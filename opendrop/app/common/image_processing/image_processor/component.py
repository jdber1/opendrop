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


from collections import OrderedDict
from typing import Any, Iterable, Callable

from gi.repository import Gtk, Gdk

from opendrop.mvp import View, Presenter, ComponentSymbol
from opendrop.mvp.typing import ComponentFactory
from opendrop.utility.bindable.typing import Bindable
from opendrop.widgets.canvas import Canvas, CanvasAlign
from .tool_panel.component import tool_panel_cs, ToolItemRef

image_processor_cs = ComponentSymbol()  # type: ComponentSymbol[Gtk.Widget]


@image_processor_cs.view(options=['tool_ids', 'plugins'])
class ImageProcessorView(View['ImageProcessorPresenter', Gtk.Widget]):
    def _do_init(self, tool_ids: Iterable[Any], plugins: Iterable[ComponentFactory]) -> Gtk.Widget:
        self._widget = Gtk.Grid()

        self._canvas = Canvas(align=CanvasAlign.FIT, can_focus=True, hexpand=True, vexpand=True)
        self._canvas.add_events(
            Gdk.EventMask.POINTER_MOTION_MASK
            | Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.BUTTON_RELEASE_MASK
            | Gdk.EventMask.ENTER_NOTIFY_MASK
            | Gdk.EventMask.LEAVE_NOTIFY_MASK
            | Gdk.EventMask.KEY_PRESS_MASK
        )

        self._canvas.show()
        self._widget.attach(self._canvas, 0, 0, 2, 1)

        extras_area = Gtk.Grid(hexpand=True, halign=Gtk.Align.END, vexpand=False, margin=5)
        extras_area.show()
        self._widget.attach(extras_area, 1, 1, 1, 1)

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
                        canvas=self._canvas,
                        extras_area=extras_area,
                        do_get_tool_item=self._get_tool_item,
                    )
                )
            )

        self._tool_panel_area.show()
        self._widget.attach(self._tool_panel_area, 0, 1, 1, 1)

        self._widget.show()

        return self._widget

    def _get_tool_item(self, tool_id: Any) -> ToolItemRef:
        return self._tool_item_refs[tool_id]

    def _do_destroy(self) -> None:
        self._widget.destroy()


class ImageProcessorPluginViewContext:
    def __init__(
            self,
            canvas: Canvas,
            extras_area: Gtk.Grid,
            do_get_tool_item: Callable[[Any], ToolItemRef]
    ) -> None:
        self.canvas = canvas
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
