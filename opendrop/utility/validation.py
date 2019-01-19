# A mish mash of functions that have something to do with input validation. (todo: refactor this)

import itertools
import math
from enum import Enum
from typing import Set, Sized, Any, Callable, Iterable

from gi.repository import Gtk

from opendrop.utility.bindable import bindable_function, SetBindable


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


@bindable_function
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
