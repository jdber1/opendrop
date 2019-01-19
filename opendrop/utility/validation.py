# A mish mash of functions that have something to do with input validation. (todo: refactor this)

import itertools
import math
from enum import Enum
from typing import Set, Sized, Any, Callable, Iterable, TypeVar, Generic, Optional

from gi.repository import Gtk

from opendrop.utility.bindable import bindable_function, SetBindable, AtomicBindableVar, if_expr, \
    BuiltinSetBindable
from opendrop.utility.bindable.bindable import Bindable
from opendrop.utility.events import Event


class ValidationFlag(Enum):
    CANNOT_BE_EMPTY = 0
    MUST_BE_POSITIVE = 1


@bindable_function
def message_from_flags(field_name: str, flags: Set[ValidationFlag]) -> str:
    if len(flags) == 0:
        return ''

    message = field_name + ' '

    if ValidationFlag.CANNOT_BE_EMPTY in flags:
        message += 'cannot be empty'
    elif ValidationFlag.MUST_BE_POSITIVE in flags:
        message += 'must be greater than 0'
    else:
        message += 'is invalid'

    return message


def check_is_not_empty(x: Any) -> Iterable[ValidationFlag]:
    if x is None or isinstance(x, Sized) and len(x) == 0:
        return (ValidationFlag.CANNOT_BE_EMPTY,)
    else:
        return tuple()


def check_is_positive(x: float) -> Iterable[ValidationFlag]:
    if x is None:
        return tuple()

    flags = []

    if not math.isfinite(x):
        flags.append(ValidationFlag.MUST_BE_POSITIVE)

    if x <= 0:
        flags.append(ValidationFlag.MUST_BE_POSITIVE)

    return flags


@bindable_function(autobind_return=BuiltinSetBindable)
def validate(value: Any, checks: Iterable[Callable[[Any], Iterable[ValidationFlag]]], enabled: bool = True) \
        -> Set[ValidationFlag]:
    if not enabled:
        return set()

    flags = {*itertools.chain(*(check(value) for check in checks))}
    flags.discard(None)
    return flags


class AssociateStyleClassToWidgetWhenFlagsPresent:
    def __init__(self, widget: Gtk.Widget, style_class: str, flags: SetBindable[ValidationFlag]) -> None:
        self._widget = widget
        self._style_class = style_class
        self._flags = flags

        self._flags.on_add.connect(self._hdl_enabled_changed, ignore_args=True)
        self._flags.on_discard.connect(self._hdl_enabled_changed, ignore_args=True)
        self._hdl_enabled_changed()

    def _hdl_enabled_changed(self) -> None:
        if len(self._flags) > 0:
            self._widget.get_style_context().add_class(self._style_class)
        else:
            self._widget.get_style_context().remove_class(self._style_class)


add_style_class_when_flags = AssociateStyleClassToWidgetWhenFlagsPresent

ValueType = TypeVar('ValueType', bound=Bindable)
ErrorType = TypeVar('ErrorType')


class FieldView(Generic[ValueType, ErrorType]):
    def __init__(self, value: ValueType, *, errors_out: Optional[SetBindable[ErrorType]] = None,
                 on_user_finished_editing: Optional[Event] = None) -> None:
        if errors_out is None:
            errors_out = BuiltinSetBindable()

        if on_user_finished_editing is None:
            on_user_finished_editing = Event()

        self.value = value
        self.errors_out = errors_out
        self.on_user_finished_editing = on_user_finished_editing


class FieldPresenter(Generic[ValueType, ErrorType]):
    def __init__(self, value: ValueType, errors: SetBindable[ErrorType], field_view: FieldView) -> None:
        self._errors = errors
        self._field_view = field_view
        self.__destroyed = False
        self.__cleanup_tasks = []

        self._is_showing_errors = AtomicBindableVar(False)
        errors_out = if_expr(cond=self._is_showing_errors, true=errors, false=BuiltinSetBindable())

        data_bindings = [
            value.bind_to(field_view.value),
            errors_out.bind_to(field_view.errors_out)]
        self.__cleanup_tasks.extend(db.unbind for db in data_bindings)

        event_connections = [
            field_view.on_user_finished_editing.connect(self._hdl_field_view_user_finished_editing)]
        self.__cleanup_tasks.extend(ec.disconnect for ec in event_connections)

    def _hdl_field_view_user_finished_editing(self) -> None:
        self._is_showing_errors.set(bool(self._errors))

    def show_errors(self) -> None:
        self._is_showing_errors.set(True)

    def destroy(self) -> None:
        assert not self.__destroyed
        for f in self.__cleanup_tasks:
            f()
        self.__destroyed = True
