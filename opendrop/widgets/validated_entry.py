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
from typing import TypeVar

from gi.repository import Gtk, GObject, Gdk

T = TypeVar('T')


# Can't inherit from Generic[T] because of conflicting metaclasses.
#
# Need to re-inherit from Gtk.Editable so that `ValidatedEntry.do_insert_text()` doesn't "overwrite the default handler"
# see https://stackoverflow.com/q/48634804/8944057
class ValidatedEntry(Gtk.Entry, Gtk.Editable):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # For some reason, if we override `do_focus_out_event()`, when switching stacks (in a Gtk.Stack) with an empty
        # ValidatedEntry widget, a warning is thrown:
        #   (__init__.py:20612): Gtk-WARNING **: GtkEntry - did not receive focus-out-event. If you connect a handler to
        #   this signal, it must return GDK_EVENT_PROPAGATE so the entry gets the event as well ...
        self.connect('focus-out-event', self.on_focus_out_event)

        # Invoke the setter
        self.value = self.value

    @abstractmethod
    def validate(self, text: str) -> bool: pass

    @abstractmethod
    def t_from_str(self, text: str) -> T: pass

    def str_from_t(self, value: T) -> str:
        return str(value)

    def restrict(self, value: T) -> T:
        return value

    def on_focus_out_event(self, widget: Gtk.Widget, event: Gdk.EventFocus) -> None:
        self._poke_value()

    def do_delete_text(self, start_pos, end_pos) -> None:
        old_text = self.get_buffer().get_text()
        new_text = old_text[:start_pos] + old_text[end_pos:]

        if not self.validate(new_text):
            self.get_buffer().delete_text(0, -1)
            return

        self.get_buffer().delete_text(start_pos, end_pos - start_pos)
        self.notify('value')

    def do_insert_text(self, insert_text: str, length: int, position: int) -> int:
        old_text = self.get_buffer().get_text()
        new_text = old_text[:position] + insert_text + old_text[position:]

        if self.validate(new_text):
            self.get_buffer().insert_text(position, insert_text, length)
            position += length

        self.notify('value')
        return position

    def do_activate(self) -> None:
        self._poke_value()

    def _poke_value(self) -> None:
        old_text = self.props.text

        self.value = self.value

        new_text = self.props.text

        if not old_text == new_text:
            self.set_position(-1)

    @GObject.Property
    def value(self) -> T:
        value = self.t_from_str(self.props.text)

        return self.restrict(value)

    @value.setter
    def value(self, value: T) -> None:
        value = self.restrict(value)

        self.props.text = self.str_from_t(value)

    get_value = value.fget
    set_value = value.fset
