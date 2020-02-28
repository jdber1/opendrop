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


from typing import Any, Mapping, Optional

from gi.repository import Gtk

from opendrop.mvp.component import ComponentSymbol, ComponentFactory
from opendrop.mvp.presenter import Presenter
from opendrop.mvp.view import View
from opendrop.utility.bindable.typing import Bindable

stack_cs = ComponentSymbol()  # type: ComponentSymbol[Gtk.Widget]


@stack_cs.view(options=['children', 'gtk_properties'])
class StackView(View['StackPresenter', Gtk.Widget]):
    def _do_init(self, children: Mapping[Any, ComponentFactory[Gtk.Widget]],
                 gtk_properties: Optional[Mapping[str, Any]] = None) -> Gtk.Widget:
        self._children = children

        # Active child component id
        self._active_child_cid = None

        # Active child stack id
        self._active_child_sid = None

        self.widget = Gtk.Grid(**(gtk_properties or {}))
        self.widget.show()

        self.presenter.view_ready()

        return self.widget

    def set_active(self, new_child_sid: Any) -> None:
        if self._active_child_sid == new_child_sid: return

        new_child_factory = self._children[new_child_sid] if new_child_sid is not None else None

        if self._active_child_cid:
            self.remove_component(self._active_child_cid)
            self._active_child_cid = None
            self._active_child_sid = None

        if new_child_factory is None: return

        self._active_child_cid, new_child_widget = self.new_component(new_child_factory)
        self._active_child_sid = new_child_sid

        new_child_widget.show()

        self.widget.add(new_child_widget)

    def _do_destroy(self):
        self.widget.destroy()


@stack_cs.presenter(options=['active_stack'])
class StackPresenter(Presenter['StackView']):
    def _do_init(self, active_stack: Bindable) -> None:
        self._active_stack = active_stack
        self.__event_connections = [
            active_stack.on_changed.connect(self._update_view)
        ]

    def view_ready(self) -> None:
        self._update_view()

    def _update_view(self) -> None:
        self.view.set_active(self._active_stack.get())

    def _do_destroy(self) -> None:
        for conn in self.__event_connections:
            conn.disconnect()
