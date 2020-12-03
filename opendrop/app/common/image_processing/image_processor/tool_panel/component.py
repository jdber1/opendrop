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


from typing import Any, Callable, MutableSequence, Mapping

from gi.repository import Gtk, Gdk

from opendrop.mvp import ComponentSymbol, View, Presenter
from opendrop.utility.bindable.typing import Bindable
from .model import ToolItemRef

tool_panel_cs = ComponentSymbol()  # type: ComponentSymbol[Gtk.Widget]


@tool_panel_cs.view(options=['tool_item_refs'])
class ToolPanelView(View['ToolPanelPresenter', Gtk.Widget]):
    STYLE = '''
    .tool-panel {
         /* background-color: gainsboro; */
         padding: 5px;
    }
    '''

    _STYLE_PROV = Gtk.CssProvider()
    _STYLE_PROV.load_from_data(bytes(STYLE, 'utf-8'))
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), _STYLE_PROV, Gtk.STYLE_PROVIDER_PRIORITY_USER)

    class _ToolItemManager:
        def __init__(self, tool_id: Any, tool_button: Gtk.ToggleButton,
                     on_click: Callable[['ToolPanelView._ToolItemManager'], Any]) -> None:
            self.tool_id = tool_id
            self._tool_button = tool_button
            self._on_click = on_click

            # Prevent the tool button from being toggled by user clicks, we only want to invoke the appropriate callback
            # when this happens. The toggled-ness of the button is managed by an outside object.
            tool_button.connect('button-press-event', lambda *_: True)

            tool_button.connect('button-release-event', self._hdl_tool_button_clicked)

        def _hdl_tool_button_clicked(self, tool_button: Gtk.Widget, event: Gdk.EventButton) -> None:
            self._on_click(self)

        @property
        def is_item_active(self) -> bool:
            return self._tool_button.props.active

        @is_item_active.setter
        def is_item_active(self, value: bool) -> None:
            self._tool_button.props.active = value

    def _do_init(self, tool_item_refs: Mapping[Any, ToolItemRef]) -> Gtk.Widget:
        self._widget = Gtk.Grid(column_spacing=5)
        self._widget.get_style_context().add_class('tool-panel')
        self._widget.show()

        #  tools_lbl = Gtk.Label('Tools:', margin=5)
        #  tools_lbl.show()
        #  self._widget.attach(tools_lbl, 0, 0, 1, 1)

        self._tools_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            homogeneous=True,
            spacing=5,
            hexpand=False,
            vexpand=False,
        )

        self._tools_box.show()
        self._widget.attach(self._tools_box, 1, 0, 1, 1)

        self._item_mgrs = []  # type: MutableSequence[self._ToolItemManager]
        for tool_id, tool_ref in tool_item_refs.items():
            self.add_item(
                tool_id=tool_id,
                tool_ref=tool_ref,
            )

        self.presenter.view_ready()

        return self._widget

    def add_item(self, tool_id: Any, tool_ref: ToolItemRef) -> None:
        new_button = Gtk.ToggleButton()
        self._tools_box.pack_start(new_button, expand=False, fill=True, padding=0)

        new_item_manager = self._ToolItemManager(
            tool_id=tool_id,
            tool_button=new_button,
            on_click=self._hdl_tool_item_clicked,
        )
        self._item_mgrs.append(new_item_manager)

        button_interior = Gtk.Grid()
        new_button.add(button_interior)

        new_button.show_all()

        tool_ref.set_referents(
            tool_id=tool_id,
            tool_button=new_button,
            tool_button_interior=button_interior,
            do_request_deactivate=self._request_deactivate_tool,
        )

    def _request_deactivate_tool(self, tool_id: Any) -> None:
        item_mgr = self._get_item_mgr_by_tool_id(tool_id)
        if item_mgr.is_item_active:
            self.presenter.activate_tool(None)

    def _hdl_tool_item_clicked(self, item_mgr: _ToolItemManager) -> None:
        # Toggle the active-ness of the clicked tool
        if not item_mgr.is_item_active:
            self.presenter.activate_tool(item_mgr.tool_id)
        else:
            self.presenter.activate_tool(None)

    def set_active_tool(self, tool_id: Any) -> None:
        for item_mgr in self._item_mgrs:
            item_mgr.is_item_active = False

        if tool_id is not None:
            item_mgr = self._get_item_mgr_by_tool_id(tool_id)
            item_mgr.is_item_active = True

    def _get_item_mgr_by_tool_id(self, tool_id: Any) -> _ToolItemManager:
        for item_mgr in self._item_mgrs:
            if item_mgr.tool_id == tool_id:
                return item_mgr
        else:
            raise ValueError(
                "No item with 'tool_id' of '{}' found"
                .format(tool_id)
            )

    def _do_destroy(self) -> None:
        self._widget.destroy()


@tool_panel_cs.presenter(options=['active_tool', 'do_activate_tool'])
class ToolPanelPresenter(Presenter['ToolPanelView']):
    def _do_init(self, active_tool: Bindable[Any], do_activate_tool: Callable[[Any], Any]) -> None:
        self._active_tool = active_tool
        self._do_activate_tool = do_activate_tool
        self.__event_connections = []

    def view_ready(self) -> None:
        self.__event_connections.extend([
            self._active_tool.on_changed.connect(self._hdl_active_tool_changed),
        ])

        self._hdl_active_tool_changed()

    def _hdl_active_tool_changed(self) -> None:
        active_tool_id = self._active_tool.get()
        self.view.set_active_tool(active_tool_id)

    def activate_tool(self, tool_id: Any) -> None:
        self._do_activate_tool(tool_id)

    def _do_destroy(self) -> None:
        for ec in self.__event_connections:
            ec.disconnect()
