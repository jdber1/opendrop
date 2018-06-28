from abc import abstractmethod
from typing import TypeVar

from gi.repository import Gtk, GObject, Gdk

T = TypeVar('T')


# Can't inherit from Generic[T] because of conflicting metaclasses.
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

    def do_insert_text(self, insert_text: str, length: int, position: int) -> int:
        old_text = self.get_buffer().get_text()
        new_text = old_text[:position] + insert_text + old_text[position:]

        if self.validate(new_text):
            self.get_buffer().insert_text(position, insert_text, length)

            return position + length
        else:
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
