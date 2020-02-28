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
# A mish mash of functions that have something to do with input validation. (todo: refactor this)
import functools
import itertools
import math
from enum import Enum
from typing import Set, Sized, Any, Callable, Iterable, TypeVar, Generic, Optional

from opendrop.utility.bindable import Bindable, BoxBindable
from opendrop.utility.bindable import apply as bn_apply
from opendrop.utility.events import Event
from opendrop.utility.geometry import Rect2


class ValidationFlag(Enum):
    INVALID = 0
    CANNOT_BE_EMPTY = 1
    MUST_BE_POSITIVE = 2


def message_from_flags(field_name: str, flags: Bindable[Set[ValidationFlag]]) -> Bindable[str]:
    return bn_apply(functools.partial(_message_from_flags, field_name), flags)


def _message_from_flags(field_name: str, flags: Set[ValidationFlag]) -> str:
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


def check_custom_condition(cond: Callable[[Any], bool]) -> Callable[[Any], Iterable[ValidationFlag]]:
    def check(x: Any) -> Iterable[ValidationFlag]:
        if not cond(x):
            return (ValidationFlag.INVALID,)
        else:
            return tuple()
    return check


def check_is_not_empty(x: Any) -> Iterable[ValidationFlag]:
    if x is None or \
            isinstance(x, Sized) and len(x) == 0 or \
            isinstance(x, Rect2) and 0 in x.size:
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


def check_is_finite(x: float) -> Iterable[ValidationFlag]:
    if x is None:
        return tuple()

    flags = []

    if not math.isfinite(x):
        flags.append(ValidationFlag.INVALID)

    return flags


def validate(value: Bindable, checks: Iterable[Callable[[Any], Iterable[ValidationFlag]]],
             enabled: Optional[Bindable[bool]] = None) -> Bindable[Set[ValidationFlag]]:
    options = {}

    if enabled is not None:
        options['enabled'] = enabled

    return bn_apply(functools.partial(_validate, checks=checks), value, **options)


def _validate(value: Any, checks: Iterable[Callable[[Any], Iterable[ValidationFlag]]], enabled: bool = True) \
        -> Set[ValidationFlag]:
    if not enabled:
        return set()

    flags = {*itertools.chain(*(check(value) for check in checks))}
    flags.discard(None)

    return flags


ValueType = TypeVar('ValueType', bound=Bindable)
ErrorType = TypeVar('ErrorType')


class FieldView(Generic[ValueType, ErrorType]):
    def __init__(self, value: ValueType, *, errors_out: Optional[Bindable[Set[ErrorType]]] = None,
                 on_user_finished_editing: Optional[Event] = None) -> None:
        if errors_out is None:
            errors_out = BoxBindable(set())  # type: Bindable[Set[ErrorType]]

        if on_user_finished_editing is None:
            on_user_finished_editing = Event()

        self.value = value
        self.errors_out = errors_out
        self.on_user_finished_editing = on_user_finished_editing


class FieldPresenter(Generic[ValueType, ErrorType]):
    def __init__(self, value: ValueType, errors: Bindable[Set[ErrorType]],
                 field_view: FieldView[ValueType, ErrorType]) -> None:
        self.__destroyed = False
        self.__cleanup_tasks = []

        self._errors = ErrorsPresenter(errors_in=errors, errors_out=field_view.errors_out)
        self.__cleanup_tasks.append(self._errors.destroy)

        data_bindings = [
            value.bind(field_view.value)]
        self.__cleanup_tasks.extend(db.unbind for db in data_bindings)

        event_connections = [
            field_view.on_user_finished_editing.connect(self.show_errors)]
        self.__cleanup_tasks.extend(ec.disconnect for ec in event_connections)

    def show_errors(self) -> None:
        self._errors.show_errors()

    def destroy(self) -> None:
        assert not self.__destroyed
        for f in self.__cleanup_tasks:
            f()
        self.__destroyed = True


class ErrorsPresenter(Generic[ErrorType]):
    def __init__(self, errors_in: Bindable[Set[ErrorType]], errors_out: Bindable[Set[ErrorType]]) -> None:
        self._errors_in = errors_in

        self.__destroyed = False
        self.__cleanup_tasks = []

        self._is_showing_errors = BoxBindable(False)
        self.__cleanup_tasks.append(lambda: self._is_showing_errors.set(False))

        data_bindings = [
            errors_out.bind_from(bn_apply(lambda x, y: x if y else set(), self._errors_in, self._is_showing_errors))]
        self.__cleanup_tasks.extend(db.unbind for db in data_bindings)

    def show_errors(self) -> None:
        self._is_showing_errors.set(bool(self._errors_in.get()))

    def destroy(self) -> None:
        assert not self.__destroyed
        for f in self.__cleanup_tasks:
            f()
        self.__destroyed = True
