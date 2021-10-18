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


from typing import Optional

from gi.repository import GObject, GLib

from opendrop.widgets.validated_entry import ValidatedEntry


class IntegerEntry(ValidatedEntry):
    __gtype_name__ = 'IntegerEntry'

    _lower = GLib.MININT
    _upper = GLib.MAXINT
    _default = 0
    _default_set = False

    @GObject.Property(type=int)
    def lower(self) -> int:
        return self._lower

    @lower.setter
    def lower(self, value: int) -> None:
        self._lower = value

    @GObject.Property(type=int)
    def upper(self) -> int:
        return self._upper

    @upper.setter
    def upper(self, value: int) -> None:
        self._upper = value

    @GObject.Property(type=int)
    def default(self) -> int:
        return self._default

    @default.setter
    def default(self, value: int) -> None:
        self._default = value
        self.default_set = True

    @GObject.Property(type=bool, default=False)
    def default_set(self) -> bool:
        return self._default_set

    @default_set.setter
    def default_set(self, value: bool) -> None:
        self._default_set = value

    def restrict(self, value: Optional[int]) -> Optional[int]:
        if value is None and self._default_set:
            value = self._default

        if value is None:
            return None

        value = max(value, self.lower)
        value = min(value, self.upper)

        return value

    def validate(self, text: str) -> bool:
        if '+' in text and self.upper is not None and self.upper < 0:
            return False
        elif '-' in text and self.lower is not None and self.lower >= 0:
            return False

        try:
            self.t_from_str(text)
            return True
        except (TypeError, ValueError):
            if text in ('+', '-'):
                return True

            return False

    def t_from_str(self, text: str) -> Optional[int]:
        if text == '':
            return None
        elif text in ('+', '-'):
            return None

        return int(text)

    def str_from_t(self, value: Optional[int]) -> str:
        if value is None:
            return ''

        return str(int(value))
