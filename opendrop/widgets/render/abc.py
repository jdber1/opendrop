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
from abc import abstractmethod
from typing import Optional

import cairo
from gi.repository import GObject

from . import protocol
from .render import Render


class RenderObject(GObject.Object, protocol.RenderObject):
    def __init__(self, **options) -> None:
        super().__init__(**options)
        self._parent = None  # type: Optional[Render]

    def draw(self, cr: cairo.Context) -> None:
        assert self._parent is not None
        self._do_draw(cr)

    @abstractmethod
    def _do_draw(self, cr: cairo.Context) -> None:
        pass

    def set_parent(self, parent: Render) -> None:
        assert self._parent is None
        self._parent = parent

    def destroy(self) -> None:
        if self._parent is None:
            return
        self._parent.remove_render_object(self)

    @GObject.Signal
    def request_draw(self) -> None:
        """Let the parent know that this object needs to be redrawn."""

    _z_index = 0

    @GObject.Property
    def z_index(self) -> int:
        return self._z_index

    @z_index.setter
    def z_index(self, value: int) -> None:
        self._z_index = value
        self.emit('request-draw')
