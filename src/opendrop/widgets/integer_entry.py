from typing import Optional

from gi.repository import GObject

from opendrop.widgets.validated_entry import ValidatedEntry


class IntegerEntry(ValidatedEntry):
    _lower = None  # type: Optional[int]
    _upper = None  # type: Optional[int]
    _default = None  # type: Optional[int]

    @GObject.Property
    def lower(self) -> Optional[int]:
        return self._lower

    @lower.setter
    def lower(self, value: Optional[int]) -> None:
        self._lower = value

    @GObject.Property
    def upper(self) -> Optional[int]:
        return self._upper

    @upper.setter
    def upper(self, value: Optional[int]) -> None:
        self._upper = value

    @GObject.Property
    def default(self) -> Optional[int]:
        return self._default

    @default.setter
    def default(self, value: Optional[int]) -> None:
        self._default = value

    def restrict(self, value: Optional[int]) -> Optional[int]:
        if value is None:
            if self.default is not None:
                return self.restrict(self.default)

            return None

        if self.lower is not None:
            value = max(value, self.lower)

        if self.upper is not None:
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
