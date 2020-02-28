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
#E. Huang, T. Denning, A. Skoufis, J. Qi, R. R. Dagastine, R. F. Tabor
#and J. D. Berry, OpenDrop: Open-source software for pendant drop
#tensiometry & contact angle measurements, submitted to the Journal of
# Open Source Software
#
#These citations help us not only to understand who is using and
#developing OpenDrop, and for what purpose, but also to justify
#continued development of this code and other open source resources.
#
# OpenDrop is distributed WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.  You
# should have received a copy of the GNU General Public License along
# with this software.  If not, see <https://www.gnu.org/licenses/>.
import weakref
from typing import Any

from gi.repository import Gtk

from opendrop.utility.bindable import Bindable


class GStyleContextClassBindable(Bindable[Any]):
    def __init__(self, style_context: Gtk.StyleContext, class_name: str) -> None:
        super().__init__()

        self._alive = True

        # See GObjectPropertyBindable for an explanation (note that Gtk.StyleContext is a GObject)
        self._style_context = style_context
        self._style_context_wr = weakref.ref(style_context)

        self._class_name = class_name

        self._hdl_style_context_changed_id = self._style_context.connect('changed', self._hdl_style_context_changed)

    def _hdl_style_context_changed(self, style_context: Gtk.StyleContext) -> None:
        if not self._alive:
            return

        self.on_changed.fire()

    def _get_value(self) -> Any:
        assert self._alive

        return self._style_context.has_class(self._class_name)

    def _set_value(self, new_value: Any) -> None:
        assert self._alive

        self._style_context.handler_block(self._hdl_style_context_changed_id)

        try:
            if bool(new_value):
                self._style_context.add_class(self._class_name)
            else:
                self._style_context.remove_class(self._class_name)
        finally:
            self._style_context.handler_unblock(self._hdl_style_context_changed_id)

    def _unlink(self, *_):
        if not self._alive:
            return

        if not self._is_style_context_garbage_collected \
                and self._style_context.handler_is_connected(self._hdl_style_context_changed_id):
            self._style_context.disconnect(self._hdl_style_context_changed_id)

        self._alive = False

    @property
    def _is_style_context_garbage_collected(self) -> bool:
        return self._style_context_wr() is None

    def __del__(self):
        self._unlink()


class GWidgetStyleClassBindable(GStyleContextClassBindable):
    def __init__(self, widget: Gtk.Widget, style_class_name: str) -> None:
        super().__init__(widget.get_style_context(), style_class_name)
