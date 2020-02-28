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
from typing import TypeVar, Callable, Any

from gi.repository import GObject

from opendrop.utility.bindable import Bindable

_T = TypeVar('_T')


class GObjectPropertyBindable(Bindable[_T]):
    def __init__(self, g_obj: GObject.Object, prop_name: str, transform_to: Callable[[_T], Any] = lambda x: x,
                 transform_from: Callable[[Any], _T] = lambda x: x) -> None:
        super().__init__()

        self._alive = True

        self._g_obj = g_obj

        # The underlying GObject can be garbage collected while the Python wrapper is still alive, we want to
        # automatically call `self._unlink()` when the underlying GObject is finalized.
        self._g_obj_wr = g_obj.weak_ref(self._unlink)

        self._prop_name = prop_name

        self._transform_to = transform_to
        self._transform_from = transform_from

        self._hdl_g_obj_notify_id = self._g_obj.connect('notify::{}'.format(prop_name), self._hdl_g_obj_notify)

    def _hdl_g_obj_notify(self, g_obj: GObject.Object, pspec: GObject.GParamSpec) -> None:
        if not self._alive:
            return

        self.on_changed.fire()

    def _get_value(self) -> Any:
        assert self._alive

        value = self._g_obj.get_property(self._prop_name)
        value = self._transform_from(value)

        return value

    def _set_value(self, new_value: Any) -> None:
        assert self._alive

        self._g_obj.handler_block(self._hdl_g_obj_notify_id)

        try:
            new_value = self._transform_to(new_value)
            self._g_obj.set_property(self._prop_name, new_value)
        finally:
            self._g_obj.handler_unblock(self._hdl_g_obj_notify_id)

    def _unlink(self, *_):
        if not self._alive:
            return

        if not self._is_g_obj_garbage_collected and self._g_obj.handler_is_connected(self._hdl_g_obj_notify_id):
            self._g_obj.disconnect(self._hdl_g_obj_notify_id)

        self._alive = False

    @property
    def _is_g_obj_garbage_collected(self) -> bool:
        return self._g_obj_wr() is None

    def __del__(self):
        self._unlink()
