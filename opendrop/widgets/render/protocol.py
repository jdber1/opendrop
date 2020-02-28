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
from enum import Enum
from typing import Optional, Any

import cairo
from gi.repository import Gdk


class Render:
    class ViewportStretch(Enum):
        FIT = 0
        FILL = 1

    def add_render_object(self, obj: 'RenderObject') -> None:
        pass

    def remove_render_object(self, obj: 'RenderObject') -> None:
        pass

    # Methods to be provided by GObject.Object or Gtk.Widget

    props = None  # type: Any

    @abstractmethod
    def emit(self, *args, **kwargs) -> None:
        """GObject.Object.emit()"""

    @abstractmethod
    def connect(self, *args, **kwargs) -> int:
        """GObject.Object.connect()"""

    @abstractmethod
    def get_window(self, *args, **kwargs) -> Optional[Gdk.Window]:
        """Gtk.Widget.get_window()"""


class RenderObject:
    def __init__(self, **options) -> None:
        super().__init__(**options)

    @abstractmethod
    def set_parent(self, parent: Render) -> None:
        pass

    @abstractmethod
    def draw(self, cr: cairo.Context) -> None:
        pass

    @abstractmethod
    def destroy(self) -> None:
        pass

    # Methods to be provided by GObject.Object

    @abstractmethod
    def emit(self, *args, **kwargs) -> None:
        """GObject.Object.emit()"""

    @abstractmethod
    def connect(self, *args, **kwargs) -> int:
        """GObject.Object.connect()"""

    @abstractmethod
    def disconnect(self, *args, **kwargs) -> int:
        """GObject.Object.disconnect()"""
